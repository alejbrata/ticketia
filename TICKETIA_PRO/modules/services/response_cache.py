import hashlib
import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)

_TTL_SECONDS = 3600   # 1 hora — suficiente para preguntas repetidas de horarios/servicios
_MAX_ENTRIES = 500    # ~500 negocios activos simultáneos


class _ResponseCache:
    """Caché en memoria con TTL para respuestas LLM informacionales (sin tool calls)."""

    def __init__(self):
        self._store: dict = {}
        self._lock = Lock()

    @staticmethod
    def _make_key(business_phone: str, message: str) -> str:
        normalized = message.lower().strip()
        return hashlib.sha256(f"{business_phone}|{normalized}".encode()).hexdigest()

    def get(self, business_phone: str, message: str) -> str | None:
        key = self._make_key(business_phone, message)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry["expires_at"]:
                del self._store[key]
                return None
            logger.debug("CACHE HIT [%s] %.60s", business_phone, message)
            return entry["response"]

    def set(self, business_phone: str, message: str, response: str) -> None:
        key = self._make_key(business_phone, message)
        with self._lock:
            if len(self._store) >= _MAX_ENTRIES:
                # Desalojar la entrada que expira antes
                oldest = min(self._store, key=lambda k: self._store[k]["expires_at"])
                del self._store[oldest]
            self._store[key] = {
                "response": response,
                "expires_at": time.monotonic() + _TTL_SECONDS,
            }
            logger.debug("CACHE SET [%s] %.60s", business_phone, message)

    def invalidate(self, business_phone: str) -> int:
        """Elimina todas las entradas de un negocio (útil al actualizar su base de conocimiento)."""
        prefix = hashlib.sha256(f"{business_phone}|".encode()).hexdigest()[:8]
        with self._lock:
            before = len(self._store)
            # No podemos filtrar por prefijo del hash, así que guardamos el phone en la entry
            to_delete = [k for k, v in self._store.items() if v.get("business_phone") == business_phone]
            for k in to_delete:
                del self._store[k]
            return before - len(self._store)

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Singleton de proceso — se comparte entre todos los workers del mismo proceso
response_cache = _ResponseCache()
