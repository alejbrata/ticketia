"""
Cliente MCP con soporte de dos transportes:

1. SSE (Server-Sent Events) — PREFERIDO en produccion
   - Requiere que mcp_server_sse.py este corriendo como proceso separado.
   - Se activa definiendo MCP_SSE_URL en .env, p.ej:
       MCP_SSE_URL=http://localhost:8001/sse
   - Ventaja: sin fork de proceso por llamada, latencia ~5 ms.

2. stdio — FALLBACK para desarrollo/testing
   - Lanza mcp_server.py como subprocess en cada llamada.
   - Sin dependencias de proceso externo, pero ~500 ms de overhead por fork.
   - Se usa automaticamente si MCP_SSE_URL no esta definida.
"""

import asyncio
import os
import json
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


class TicketiaMCPClient:
    """
    Ejecuta un loop de agente OpenAI usando herramientas expuestas via MCP.
    Selecciona automaticamente el transporte SSE o stdio segun la configuracion.
    """

    def __init__(self):
        self._openai = AsyncOpenAI()
        self._sse_url = os.environ.get('MCP_SSE_URL')  # e.g. http://localhost:8001/sse
        self._server_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mcp_server.py"
        )

    async def execute_agent_loop(self, system_prompt: str, user_message: str) -> str:
        """
        Ejecuta un turno completo del agente: LLM → tool calls → respuesta final.
        Devuelve el texto de respuesta para enviar al usuario.
        """
        if self._sse_url:
            return await self._run_with_sse(system_prompt, user_message)
        else:
            return await self._run_with_stdio(system_prompt, user_message)

    # ── SSE transport ─────────────────────────────────────────────────────────

    async def _run_with_sse(self, system_prompt: str, user_message: str) -> str:
        """Conecta al servidor MCP SSE ya en ejecucion (sin fork de proceso)."""
        try:
            from mcp.client.sse import sse_client

            async with sse_client(url=self._sse_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await self._agent_loop(session, system_prompt, user_message)

        except Exception as e:
            print(f"[MCP-SSE] Error conectando a {self._sse_url}: {e}")
            print("[MCP-SSE] Cayendo a transporte stdio como fallback...")
            return await self._run_with_stdio(system_prompt, user_message)

    # ── stdio transport ───────────────────────────────────────────────────────

    async def _run_with_stdio(self, system_prompt: str, user_message: str) -> str:
        """Lanza mcp_server.py como subprocess y se comunica por stdio."""
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[self._server_script],
                env=os.environ.copy()
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await self._agent_loop(session, system_prompt, user_message)

        except Exception as e:
            print(f"[MCP-stdio] Error: {e}")
            return f"Error del sistema al acceder a las herramientas: {e}"

    # ── Loop comun ────────────────────────────────────────────────────────────

    async def _agent_loop(
        self,
        session: ClientSession,
        system_prompt: str,
        user_message: str
    ) -> str:
        """
        Logica compartida entre SSE y stdio:
        1. Obtener lista de tools del servidor MCP.
        2. Primera llamada al LLM con las tools disponibles.
        3. Si hay tool_calls: ejecutarlas y hacer segunda llamada para sintesis.
        4. Devolver texto final.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Descubrir herramientas disponibles en el servidor MCP
        tools_response = await session.list_tools()
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                },
            }
            for t in tools_response.tools
        ]

        # Primera llamada al LLM
        response = await self._openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=openai_tools,
        )
        response_msg = response.choices[0].message
        messages.append(response_msg)

        # Ejecutar tool calls si los hay
        if response_msg.tool_calls:
            for tool_call in response_msg.tool_calls:
                print(f"[MCP] Tool solicitada: {tool_call.function.name}")
                args = json.loads(tool_call.function.arguments)

                try:
                    result = await session.call_tool(tool_call.function.name, arguments=args)
                    tool_result = result.content[0].text if result.content else "Exito sin salida."
                except Exception as e:
                    tool_result = f"Error ejecutando {tool_call.function.name}: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": tool_result,
                })

            # Segunda llamada para sintetizar los resultados de las tools
            final_response = await self._openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            return final_response.choices[0].message.content

        return response_msg.content


# ── Singleton ─────────────────────────────────────────────────────────────────

_mcp_client: TicketiaMCPClient | None = None


def get_mcp_client() -> TicketiaMCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = TicketiaMCPClient()
    return _mcp_client
