"""
Servidor MCP con transporte SSE (Server-Sent Events).

Ventaja frente al servidor stdio (mcp_server.py):
- El proceso se lanza UNA SOLA VEZ y permanece activo.
- El cliente MCP se conecta via HTTP, sin fork de proceso por cada llamada.
- Reduce la latencia de ~500 ms (fork) a ~5 ms (conexión HTTP local).
- Permite múltiples clientes concurrentes conectados al mismo servidor.

Arranque:
    python mcp_server_sse.py          (puerto 8001 por defecto)
    MCP_SSE_PORT=9000 python mcp_server_sse.py

El cliente (core/mcp_client.py) lo detecta si MCP_SSE_URL está definida:
    MCP_SSE_URL=http://localhost:8001/sse
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from mcp.server.fastmcp import FastMCP
from app import app, mail
from core.mcp_tools import (
    tool_get_financial_summary,
    tool_get_appointments,
    tool_search_web,
    tool_schedule_appointment,
    tool_send_email_notification,
    tool_get_business_stats,
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get('MCP_SSE_PORT', 8001))

mcp = FastMCP("ZeptaiDataServer-SSE", host="0.0.0.0", port=PORT)


@mcp.tool()
def get_financial_summary(user_phone: str) -> str:
    """
    Devuelve un resumen de los gastos del usuario basado en sus tickets registrados.

    Args:
        user_phone: Número de teléfono exacto del usuario en la base de datos.
    """
    return tool_get_financial_summary(user_phone, app)


@mcp.tool()
def get_appointments(owner_phone: str, days_ahead: int = 7) -> str:
    """
    Lista las próximas citas del negocio en los próximos N días.

    Args:
        owner_phone: Teléfono del propietario del negocio.
        days_ahead: Número de días hacia adelante a consultar (por defecto 7).
    """
    return tool_get_appointments(owner_phone, app, days_ahead)


@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Busca información actualizada en la web. Útil para subvenciones (BOE), noticias o conocimiento general.

    Args:
        query: La consulta de búsqueda.
        max_results: Número máximo de resultados (por defecto 5).
    """
    return tool_search_web(query, max_results)


@mcp.tool()
def schedule_appointment(
    owner_phone: str,
    date: str,
    time: str,
    client_name: str,
    client_phone: str = ""
) -> str:
    """
    Agenda una nueva cita en el calendario del negocio, comprobando conflictos.

    Args:
        owner_phone: Teléfono del propietario del negocio (dueño del calendario).
        date: Fecha de la cita en formato YYYY-MM-DD.
        time: Hora de la cita en formato HH:MM.
        client_name: Nombre del cliente.
        client_phone: Teléfono del cliente (opcional).
    """
    return tool_schedule_appointment(owner_phone, date, time, client_name, client_phone, app)


@mcp.tool()
def send_email_notification(owner_phone: str, to_email: str, subject: str, body: str) -> str:
    """
    Envía un email en nombre del negocio. Requiere el teléfono del propietario
    para verificar que existe en el sistema y registrar el envío.

    Args:
        owner_phone: Teléfono del propietario del negocio que autoriza el envío.
        to_email: Dirección de correo del destinatario.
        subject: Asunto del email.
        body: Cuerpo del email en texto plano.
    """
    return tool_send_email_notification(owner_phone, to_email, subject, body, app, mail)


@mcp.tool()
def get_business_stats(owner_phone: str) -> str:
    """
    Devuelve métricas clave del negocio: tickets del mes, citas pendientes y uso LLM reciente.

    Args:
        owner_phone: Teléfono del propietario del negocio.
    """
    return tool_get_business_stats(owner_phone, app)


if __name__ == "__main__":
    logger.info("MCP-SSE arrancando en http://0.0.0.0:%s/sse", PORT)
    mcp.run(transport="sse")
