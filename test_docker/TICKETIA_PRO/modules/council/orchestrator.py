import os
import json
import asyncio
from openai import AsyncOpenAI
from core.clients import get_openai_client
from core.mcp_client import get_mcp_client

class CouncilManager:
    def __init__(self):
        # We need an AsyncOpenAI client for the async CouncilManager
        self.client = AsyncOpenAI()
        self.mcp_client = get_mcp_client()
        
    async def run_session(self, topic, user_context, use_mcp=True):
        """
        Ejecuta una sesión de debate del Consejo.
        Devuelve un generador asíncrono para streaming.
        """
        print(f"🏛️ Council: Iniciando sesión sobre '{topic}'")
        
        # 1. Definir los Personas
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
        
        # 2. Ronda 1: Opiniones Iniciales (Paralelo o Secuencial)
        # Hacemos secuencial para dar sensación de conversación
        
        for key, p in personas.items():
            response = await self._get_agent_opinion(p, topic, user_context, transcript, use_mcp)
            transcript.append({"agent": key, "name": p['name'], "emoji": p['emoji'], "text": response})
            yield {"type": "message", "agent": key, "name": p['name'], "emoji": p['emoji'], "text": response}

        # 3. Ronda 2: Réplica / Debate (Interacción entre ellos)
        # Cada uno lee lo que han dicho los demás y añade un matiz o crítica
        for key, p in personas.items():
            # Solo réplica si tiene algo interesante que añadir (simulado siempre por ahora)
            response = await self._get_agent_rebuttal(p, topic, transcript)
            if response:
                transcript.append({"agent": key, "name": p['name'], "emoji": p['emoji'], "text": response})
                yield {"type": "message", "agent": key, "name": p['name'], "emoji": p['emoji'], "text": response}
            
        # 4. Ronda 3: Síntesis / Plan de Acción (El Coach suele moderar)
        final_plan = await self._generate_synthesis(topic, transcript)
        yield {"type": "plan", "text": final_plan}

    async def _get_agent_opinion(self, persona, topic, user_context, history, use_mcp: bool):
        """Genera la opinión de un agente específico."""
        
        history_text = "\n".join([f"{m['name']}: {m['text']}" for m in history])
        
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
        Sé breve (max 30 palabras) a menos que uses una herramienta para buscar información (en ese caso puedes ser un poco más largo).
        """
        
        try:
            if use_mcp:
                # Use the MCP client execution loop
                return await self.mcp_client.execute_agent_loop(system_prompt=prompt, user_message=topic)
            else:
                resp = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"Error ({persona['name']}): {e}"

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
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8 # Un poco más creativo para el debate
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return None

    async def _generate_synthesis(self, topic, transcript):
        """Genera un plan de acción final."""
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
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return "Error generando conclusiones."
