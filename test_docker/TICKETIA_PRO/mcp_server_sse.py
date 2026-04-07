import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from mcp.server.fastmcp import FastMCP
from core.db_models import db, Ticket
from app import app as flask_app

# Create the FastMCP Server
# By default, FastMCP when run via CLI or programmatically can be inspected.
# However, FastMCP also provides a `.create_app()` method to mount it on Starlette/FastAPI
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
        with flask_app.app_context():
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

# FastMCP can run an SSE server directly
if __name__ == "__main__":
    mcp.run(transport="sse")
