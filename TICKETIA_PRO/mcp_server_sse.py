"""
Servidor MCP con transporte SSE (Server-Sent Events).

Ventaja frente al servidor stdio (mcp_server.py):
- El proceso se lanza UNA SOLA VEZ y permanece activo.
- El cliente MCP se conecta via HTTP, sin fork de proceso por cada llamada.
- Reduce la latencia de ~500 ms (fork) a ~5 ms (conexion HTTP local).
- Permite multiples clientes concurrentes conectados al mismo servidor.

Arranque:
    python mcp_server_sse.py          (puerto 8001 por defecto)
    MCP_SSE_PORT=9000 python mcp_server_sse.py

El cliente (core/mcp_client.py) lo detecta si MCP_SSE_URL esta definida:
    MCP_SSE_URL=http://localhost:8001/sse
"""

import os
import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from mcp.server.fastmcp import FastMCP
from core.db_models import db, Ticket, Appointment
from app import app, mail
from flask_mail import Message
from duckduckgo_search import DDGS

PORT = int(os.environ.get('MCP_SSE_PORT', 8001))

mcp = FastMCP("TicketiaDataServer-SSE")


# ─── Tool 1: Resumen financiero ───────────────────────────────────────────────

@mcp.tool()
def get_financial_summary(user_phone: str) -> str:
    """
    Devuelve un resumen de los gastos del usuario basado en sus tickets registrados.

    Args:
        user_phone: Numero de telefono exacto del usuario en la base de datos.
    """
    try:
        with app.app_context():
            tickets = Ticket.query.filter_by(user_phone=user_phone).all()

            if not tickets:
                return f"No se han encontrado tickets para el usuario {user_phone}."

            total = 0.0
            lines = []
            for t in tickets:
                amount = t.total if t.total else 0.0
                total += amount
                date_str = t.date.strftime('%Y-%m-%d') if t.date else "Fecha desconocida"
                concept = t.concept if t.concept else "Gasto sin concepto"
                lines.append(f"- {date_str}: {concept} ({amount:.2f}€)")

            summary = f"Resumen Financiero para {user_phone}\n"
            summary += f"Total gastado: {total:.2f}€ en {len(tickets)} tickets.\n\n"
            summary += "Desglose reciente:\n"
            summary += "\n".join(lines[:5])
            if len(tickets) > 5:
                summary += f"\n... y {len(tickets) - 5} tickets mas."
            return summary

    except Exception as e:
        return f"Error al consultar la base de datos: {e}"


# ─── Tool 2: Busqueda web ─────────────────────────────────────────────────────

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Busca informacion actualizada en la web. Util para subvenciones (BOE), noticias o conocimiento general.

    Args:
        query: La consulta de busqueda.
        max_results: Numero maximo de resultados (por defecto 5).
    """
    try:
        results = ""
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))

        if not search_results:
            return f"No se encontraron resultados para: '{query}'."

        for i, r in enumerate(search_results, 1):
            results += f"{i}. {r.get('title', 'Sin titulo')}\n"
            results += f"   Enlace: {r.get('href', 'N/A')}\n"
            results += f"   Resumen: {r.get('body', 'Sin resumen')}\n\n"

        return f"Resultados para '{query}':\n\n{results}"

    except Exception as e:
        return f"Error al buscar en la web: {e}"


# ─── Tool 3: Agendar cita ─────────────────────────────────────────────────────

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
        owner_phone: Telefono del propietario del negocio (dueno del calendario).
        date: Fecha de la cita en formato YYYY-MM-DD.
        time: Hora de la cita en formato HH:MM.
        client_name: Nombre del cliente.
        client_phone: (Opcional) Telefono del cliente.
    """
    try:
        with app.app_context():
            existing = Appointment.query.filter_by(
                business_phone=owner_phone,
                date=date,
                time=time
            ).first()

            if existing:
                return f"Ya existe una cita a las {time} el {date}."

            new_appt = Appointment(
                business_phone=owner_phone,
                date=date,
                time=time,
                client_name=client_name,
                client_phone=client_phone
            )
            db.session.add(new_appt)
            db.session.commit()

            return f"Cita agendada para {client_name} el {date} a las {time}."

    except Exception as e:
        return f"Error al agendar cita: {e}"


# ─── Tool 4: Enviar email ─────────────────────────────────────────────────────

@mcp.tool()
def send_email_notification(to_email: str, subject: str, body: str) -> str:
    """
    Envia un email en nombre del negocio.

    Args:
        to_email: Direccion de correo del destinatario.
        subject: Asunto del email.
        body: Cuerpo del email en texto plano.
    """
    try:
        with app.app_context():
            msg = Message(
                subject=subject,
                sender=app.config.get('MAIL_DEFAULT_SENDER', 'ticketia.soporte@gmail.com'),
                recipients=[to_email],
                body=body
            )
            mail.send(msg)
            return f"Correo enviado a {to_email} con asunto '{subject}'."

    except Exception as e:
        return f"Error al enviar el correo: {e}"


# ─── Arranque ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[MCP-SSE] Servidor arrancando en http://0.0.0.0:{PORT}/sse")
    print("[MCP-SSE] Define MCP_SSE_URL=http://localhost:{PORT}/sse en .env para que el cliente lo use.")
    mcp.run(transport="sse", host="0.0.0.0", port=PORT)
