import os
import json
import logging
import time as _time
import asyncio
from openai import AsyncOpenAI
from core.clients import get_openai_client
from core.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


class CouncilManager:
    def __init__(self):
        self.client = AsyncOpenAI()
        self.mcp_client = get_mcp_client()

    async def run_session(self, topic, user_context, use_mcp=True, owner_phone=None):
        """
        Ejecuta una sesión de debate del Consejo.
        Devuelve un generador asíncrono para streaming.
        """
        logger.info("Council: iniciando sesión sobre '%s'", topic)

        personas = {
            "socio": {
                "name": "El Socio",
                "role": "Growth & Ventas",
                "emoji": "🐯",
                "style": "Agresivo, enfocado en ingresos, impaciente. Frases cortas.",
                "goal": "Maximizar ventas YA."
            },
            "gestor": {
                "name": "El Gestor",
                "role": "Legal & Fiscal",
                "emoji": "🦉",
                "style": "Conservador, técnico, preocupado por riesgos y Hacienda.",
                "goal": "Evitar multas y asegurar viabilidad financiera."
            },
            "coach": {
                "name": "El Coach",
                "role": "Productividad",
                "emoji": "🚀",
                "style": "Práctico, empático, enfocado en el tiempo del dueño.",
                "goal": "Que el dueño trabaje menos y mejor."
            }
        }

        transcript = []

        # Ronda 1: Opiniones iniciales
        for key, p in personas.items():
            yield {"type": "typing", "agent": key, "name": p['name'], "emoji": p['emoji']}
            response = await self._get_agent_opinion(p, topic, user_context, transcript, use_mcp, owner_phone)
            transcript.append({"agent": key, "name": p['name'], "emoji": p['emoji'], "text": response})
            yield {"type": "message", "agent": key, "name": p['name'], "emoji": p['emoji'], "text": response, "round": 1}
            await asyncio.sleep(0.8)  # pausa para que el usuario lea el mensaje

        # Separador de ronda
        yield {"type": "divider", "text": "💬 Debate — réplicas"}

        # Ronda 2: Réplicas / Debate
        for key, p in personas.items():
            yield {"type": "typing", "agent": key, "name": p['name'], "emoji": p['emoji']}
            response = await self._get_agent_rebuttal(p, topic, transcript)
            if response:
                transcript.append({"agent": key, "name": p['name'], "emoji": p['emoji'], "text": response})
                yield {"type": "message", "agent": key, "name": p['name'], "emoji": p['emoji'], "text": response, "round": 2}
                await asyncio.sleep(0.6)

        # Ronda 3: Síntesis / Plan de acción
        yield {"type": "divider", "text": "📝 Conclusión del Consejo"}
        yield {"type": "typing", "agent": "system", "name": "Secretario", "emoji": "📝"}
        final_plan = await self._generate_synthesis(topic, transcript)
        yield {"type": "plan", "text": final_plan}

    async def _get_agent_opinion(self, persona, topic, user_context, history, use_mcp: bool, owner_phone=None):
        """Genera la opinión de un agente específico."""
        history_text = "\n".join([f"{m['name']}: {m['text']}" for m in history])

        email_constraint = (
            f"\nIMPORTANTE: Si usas la herramienta send_email_notification, "
            f"el argumento owner_phone DEBE ser siempre '{owner_phone}'."
        ) if owner_phone else ""

        prompt = f"""
        Eres {persona['name']} ({persona['emoji']}).
        Tu rol es {persona['role']}.
        Tu personalidad es: {persona['style']}
        Tu objetivo: {persona['goal']}

        Contexto del Usuario: {user_context}

        Dilema: "{topic}"

        Debate previo:
        {history_text}

        Opina sobre el dilema desde TU punto de vista.
        Si alguien ya habló, puedes estar de acuerdo o (mejor) discrepar si va contra tus principios.
        Sé breve (max 30 palabras) a menos que uses una herramienta para buscar información.
        {email_constraint}
        """

        try:
            if use_mcp:
                return await self.mcp_client.execute_agent_loop(system_prompt=prompt, user_message=topic)
            else:
                _t0 = _time.time()
                resp = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                self._track("gpt-4o", "council_opinion", resp, int((_time.time() - _t0) * 1000))
                return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Council opinion error (%s): %s", persona['name'], e)
            return f"[{persona['name']} no pudo responder]"

    async def _get_agent_rebuttal(self, persona, topic, history):
        """Genera una réplica o matiz viendo lo que han dicho los otros."""
        history_text = "\n".join([f"{m['name']}: {m['text']}" for m in history])

        prompt = f"""
        Eres {persona['name']} ({persona['emoji']}).
        Tu rol es {persona['role']}.

        Dilema Original: "{topic}"

        Han dicho esto hasta ahora:
        {history_text}

        REACT:
        Lee las opiniones de tus compañeros.
        Si dijeron algo peligroso o erróneo según TU criterio, corrígeles o matiza.
        Si estás de acuerdo, añade un "Sí, y además...".
        NO te repitas. Aporta valor nuevo.
        Sé muy breve (max 25 palabras).
        """

        try:
            _t0 = _time.time()
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8
            )
            self._track("gpt-4o", "council_rebuttal", resp, int((_time.time() - _t0) * 1000))
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Council rebuttal error (%s): %s", persona['name'], e)
            return None

    async def _generate_synthesis(self, topic, transcript):
        """Genera un plan de acción final consensuado."""
        history_text = "\n".join([f"{m['name']}: {m['text']}" for m in transcript])

        prompt = f"""
        Actúa como Secretario del Consejo.

        Dilema Original: "{topic}"

        Opiniones:
        {history_text}

        Genera un "Plan de Acción Consensuado" en Markdown.
        1. Decisión Recomendada.
        2. Pasos a seguir (Lista).
        3. Advertencia final (si aplica).

        Sé directo y útil para un autónomo.
        """

        try:
            _t0 = _time.time()
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            self._track("gpt-4o", "council_synthesis", resp, int((_time.time() - _t0) * 1000))
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Council synthesis error: %s", e)
            return "Error generando conclusiones."

    def _track(self, model: str, stage: str, response, latency_ms: int) -> None:
        """Registra la llamada en la BD de métricas (best-effort)."""
        try:
            from core.llm_tracker import track
            track(None, model, stage, response, latency_ms)
        except Exception as e:
            logger.debug("Council tracking error (non-critical): %s", e)
