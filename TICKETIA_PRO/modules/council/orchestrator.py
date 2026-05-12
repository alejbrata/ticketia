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
                "style": (
                    "Hablas como un founder que ha levantado tres empresas. "
                    "Piensas que el mayor riesgo no es crecer rápido, sino quedarte quieto mientras la competencia te come. "
                    "Usas datos: CAC, LTV, pipeline, conversión. "
                    "Te irrita la parálisis por análisis. Cuando alguien dice 'hay que tener cuidado', "
                    "lo traduces como 'tengo miedo de actuar'. "
                    "Frases cortas, ritmo rápido, a veces cortante."
                ),
                "goal": "Generar ingresos en los próximos 90 días. Todo lo demás es secundario."
            },
            "gestor": {
                "name": "El Gestor",
                "role": "Legal & Fiscal",
                "emoji": "🦉",
                "style": (
                    "Llevas 20 años viendo negocios quebrar por saltarse los fundamentos fiscales y legales. "
                    "Hablas de Hacienda, de la AEAT, de modelos 303 y 347, de contingencias. "
                    "No eres un aguafiestas: eres el que salva el negocio cuando los demás ya se fueron a casa. "
                    "Te pone nervioso cuando alguien propone gastar antes de tener claro el flujo de caja. "
                    "Tono técnico, algo seco, con ejemplos de casos reales de empresas que lo hicieron mal."
                ),
                "goal": "Que el negocio siga abierto dentro de 3 años y no tenga una inspección encima."
            },
            "coach": {
                "name": "El Coach",
                "role": "Operaciones & Dueño",
                "emoji": "🚀",
                "style": (
                    "Tu obsesión es el dueño del negocio, no el negocio. "
                    "Preguntas incómodas: '¿tiene el equipo para ejecutar eso?', '¿cuántas horas más puede aguantar?', "
                    "'¿qué pasa si esto funciona y no pueden atender la demanda?'. "
                    "Crees que el Socio vende humo a veces y que el Gestor bloquea por miedo. "
                    "Tu rol es aterrizar las ideas a la realidad operativa del día a día. "
                    "Directo, empático pero sin filtros cuando algo no tiene sentido."
                ),
                "goal": "Que el plan sea ejecutable por una persona real con recursos limitados, sin quemarse."
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
Eres {persona['name']} ({persona['emoji']}), {persona['role']}.

QUIÉN ERES:
{persona['style']}

TU OBJETIVO EN ESTE CONSEJO:
{persona['goal']}

CONTEXTO DEL NEGOCIO:
{user_context}

TEMA QUE SE DEBATE:
"{topic}"

{"LO QUE YA HAN DICHO TUS COMPAÑEROS:" + chr(10) + history_text if history_text else "Eres el primero en hablar."}

DA TU OPINIÓN:
- Habla en primera persona, con tu voz y tu carácter. Sin presentarte.
- Si alguien ya ha opinado y va en contra de tus principios, discrepa con nombre y argumento.
- Aporta algo concreto: un dato, un riesgo real, una acción específica. Nada de generalidades.
- Entre 40 y 70 palabras. Sin bullet points. Párrafo directo.
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
                    max_tokens=250,
                    temperature=0.9
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
Eres {persona['name']} ({persona['emoji']}), {persona['role']}.

QUIÉN ERES:
{persona['style']}

Tema: "{topic}"

Lo que se ha dicho hasta ahora:
{history_text}

RÉPLICA — esto es un debate real, no una reunión de empresa:
- Cita a un compañero por su nombre si vas a contradecirle o matizarle.
- Di exactamente qué parte de lo que dijeron es incompleta, ingenua o peligrosa según TU criterio.
- Añade algo que aún no se ha dicho: un ejemplo, un número, una consecuencia concreta.
- Sin diplomacia innecesaria. Sin introducciones. Primera palabra ya es argumento.
- Entre 30 y 50 palabras.
"""

        try:
            _t0 = _time.time()
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.95
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
Eres el Secretario del Consejo. Tu trabajo es sintetizar el debate y dar una recomendación real, no un documento corporativo.

Tema debatido: "{topic}"

Debate completo:
{history_text}

Escribe el plan en Markdown con esta estructura EXACTA:

## Veredicto
Una frase clara que diga qué hacer. No "hay que equilibrar". Elige una dirección.

## Por qué
2-3 frases que expliquen el razonamiento, integrando los puntos más sólidos del debate.
Menciona qué argumento del debate ha sido el más determinante.

## Los 3 primeros pasos
Lista de exactamente 3 acciones concretas, ordenadas por prioridad, con un plazo aproximado cada una.
Que las pueda ejecutar una persona sola en las próximas semanas.

## El riesgo principal a vigilar
Una sola cosa. La que más podría torcer el plan si no se controla.

Sin introducciones. Sin títulos extra. Sin relleno.
"""

        try:
            _t0 = _time.time()
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
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
