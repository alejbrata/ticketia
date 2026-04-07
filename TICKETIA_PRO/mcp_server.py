from mcp.server.fastmcp import FastMCP
from core.db_models import db, Ticket, Appointment
from app import app, mail
from flask_mail import Message
from duckduckgo_search import DDGS
import datetime

# Initialize FastMCP Server
mcp = FastMCP("TicketiaDataServer")

@mcp.tool()
def get_financial_summary(user_phone: str) -> str:
    """
    Get a summary of a user's expenses based on their registered tickets.
    
    Args:
        user_phone: The exact phone number of the user in the database.
    """
    try:
        # Run inside the Flask application context to access SQLAlchemy
        with app.app_context():
            # Query the database
            tickets = Ticket.query.filter_by(user_phone=user_phone).all()
            
            if not tickets:
                return f"No se han encontrado tickets o gastos financiados para el usuario {user_phone}."

            total_expenses = 0.0
            ticket_details = []
            
            for t in tickets:
                amount = t.total if t.total else 0.0
                total_expenses += amount
                date_str = t.date.strftime('%Y-%m-%d') if t.date else "Fecha Desconocida"
                concept_str = t.concept if t.concept else "Gasto sin concepto"
                ticket_details.append(f"- {date_str}: {concept_str} ({amount:.2f}€)")

            summary = f"💰 **Resumen Financiero para {user_phone}** 💰\n"
            summary += f"Total Gastado: {total_expenses:.2f}€ en {len(tickets)} tickets.\n\n"
            summary += "**Desglose reciente:**\n"
            summary += "\n".join(ticket_details[:5]) # Show up to 5 tickets
            
            if len(tickets) > 5:
                summary += f"\n... y {len(tickets) - 5} tickets más."
                
            return summary
            
    except Exception as e:
        return f"Error al consultar la base de datos: {str(e)}"

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web for real-time information. Useful for finding latest news, grants (e.g. BOE), or general knowledge.
    
    Args:
        query: The search query to look up on the web.
        max_results: Maximum number of results to return (default 5).
    """
    try:
        results = ""
        with DDGS() as ddgs:
            # text() returns an iterator of dictionaries like {'title': ..., 'href': ..., 'body': ...}
            search_results = list(ddgs.text(query, max_results=max_results))
            
            if not search_results:
                return f"No se encontraron resultados para la búsqueda: '{query}'."
                
            for i, r in enumerate(search_results):
                results += f"{i+1}. **{r.get('title', 'Sin Título')}**\n"
                results += f"   - Enlace: {r.get('href', 'N/A')}\n"
                results += f"   - Resumen: {r.get('body', 'Sin resumen')}\n\n"
                
        return f"Resultados de búsqueda web para '{query}':\n\n{results}"
    except Exception as e:
         return f"Error al buscar en la web: {str(e)}"

@mcp.tool()
def schedule_appointment(owner_phone: str, date: str, time: str, client_name: str, client_phone: str = "") -> str:
    """
    Schedule a new appointment/meeting in the business calendar.
    
    Args:
        owner_phone: The exact phone number of the business owner (who owns the calendar).
        date: The date of the appointment in YYYY-MM-DD format.
        time: The time of the appointment in HH:MM format.
        client_name: The name of the client/person the meeting is with.
        client_phone: (Optional) The phone number of the client.
    """
    try:
        with app.app_context():
            # Check for existing appointment
            existing = Appointment.query.filter_by(
                business_phone=owner_phone,
                date=date,
                time=time
            ).first()
            
            if existing:
                return f"⚠️ Ya existe una cita programada a las {time} el día {date}."
                
            # Create a new appointment
            new_appt = Appointment(
                business_phone=owner_phone,
                date=date,
                time=time,
                client_name=client_name,
                client_phone=client_phone
            )
            db.session.add(new_appt)
            db.session.commit()
            
            return f"✅ Cita agendada correctamente para {client_name} el día {date} a las {time}."
    except Exception as e:
        return f"Error al agendar cita: {str(e)}"

@mcp.tool()
def send_email_notification(to_email: str, subject: str, body: str) -> str:
    """
    Send an email to a specific address on behalf of the business.
    
    Args:
        to_email: The recipient's email address.
        subject: The subject of the email.
        body: The plain text content of the email.
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
            return f"📧 Correo electrónico enviado correctamente a {to_email} con el asunto '{subject}'."
    except Exception as e:
        return f"Error al enviar el correo: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP server on stdio
    # Note: When running over stdio, all print statements go to the client.
    # FastMCP uses sys.stdout for the protocol.
    mcp.run()
