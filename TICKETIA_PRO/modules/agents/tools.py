from datetime import datetime, date as date_type
from core.db_models import db, Appointment


def _parse_date(date_str: str) -> date_type:
    """Convierte string 'YYYY-MM-DD' a datetime.date. Lanza ValueError si el formato es incorrecto."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class CalendarTools:
    """Herramientas de calendario que operan contra la base de datos."""

    ALL_SLOTS = ["09:00", "10:00", "11:00", "12:00", "13:00", "16:00", "17:00", "18:00"]

    @staticmethod
    def check_availability(date: str, business_phone: str) -> str:
        """
        Consulta disponibilidad real para una fecha dada.
        date debe venir como 'YYYY-MM-DD'.
        """
        try:
            parsed_date = _parse_date(date)
        except ValueError:
            return f"Formato de fecha incorrecto: '{date}'. Usa YYYY-MM-DD."

        existing = Appointment.query.filter_by(
            business_phone=business_phone,
            date=parsed_date
        ).all()

        busy_times = {appt.time for appt in existing}
        available_slots = [s for s in CalendarTools.ALL_SLOTS if s not in busy_times]

        if not available_slots:
            return "No quedan huecos disponibles para esa fecha."

        return f"Huecos disponibles el {date}: {', '.join(available_slots)}"

    @staticmethod
    def book_appointment(date: str, time: str, client_name: str, phone: str, business_phone: str) -> str:
        """
        Reserva una cita. Realiza doble verificación de conflictos.
        date debe venir como 'YYYY-MM-DD'.
        """
        try:
            parsed_date = _parse_date(date)
        except ValueError:
            return f"Formato de fecha incorrecto: '{date}'. Usa YYYY-MM-DD."

        existing = Appointment.query.filter_by(
            business_phone=business_phone,
            date=parsed_date,
            time=time
        ).first()

        if existing:
            return f"El horario de las {time} ya está ocupado. Por favor elige otro."

        new_appt = Appointment(
            business_phone=business_phone,
            date=parsed_date,
            time=time,
            client_name=client_name,
            client_phone=phone
        )

        try:
            db.session.add(new_appt)
            db.session.commit()
            return f"Cita confirmada para el {date} a las {time}. ¡Te esperamos, {client_name}!"
        except Exception as e:
            db.session.rollback()
            print(f"Error DB book_appointment: {e}")
            return "Hubo un error al guardar la cita. Por favor intenta más tarde."


# ---------------------------------------------------------------------------
# Esquema para OpenAI Function Calling
# ---------------------------------------------------------------------------
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Consulta los horarios disponibles para una fecha específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "La fecha a consultar en formato YYYY-MM-DD."
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Reserva una cita en el calendario para un cliente específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Fecha de la cita (YYYY-MM-DD)."},
                    "time": {"type": "string", "description": "Hora de la cita (HH:MM)."},
                    "client_name": {"type": "string", "description": "Nombre del cliente."},
                    "phone": {"type": "string", "description": "Teléfono de contacto del cliente."}
                },
                "required": ["date", "time", "client_name", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_proposal_from_last_image",
            "description": "Utiliza la última imagen subida (nota manuscrita o servilleta) para redactar un presupuesto formal en PDF.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_proposal_from_text",
            "description": "Genera un presupuesto PDF formal directamente desde datos proporcionados por texto o voz. IMPORTANTE: si el usuario no indica precios, debes estimarlos con precios de mercado razonables para España. Nunca uses 0 como precio — siempre pon un valor estimado realista.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nombre del cliente."},
                    "items": {
                        "type": "array",
                        "description": "Lista de items/servicios. El campo 'price' es OBLIGATORIO y debe ser mayor que 0. Si el usuario no indicó precio, estima un precio de mercado realista para España.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "desc": {"type": "string", "description": "Descripción del servicio"},
                                "qty": {"type": "integer", "description": "Cantidad"},
                                "price": {"type": "number", "description": "Precio unitario en EUR. OBLIGATORIO, nunca 0. Estima precio de mercado si no se indica."},
                                "total": {"type": "number", "description": "Total de línea (qty * price)"}
                            },
                            "required": ["desc", "qty", "price", "total"]
                        }
                    },
                    "total": {"type": "number", "description": "Total del presupuesto."},
                    "notes": {"type": "string", "description": "Notas adicionales."}
                },
                "required": ["client_name", "items", "total"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_marketing_material",
            "description": "Crea material visual de marketing (imágenes publicitarias o diapositivas PPT).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Descripción del contenido a generar."},
                    "format": {
                        "type": "string",
                        "enum": ["image", "slide"],
                        "description": "'image' para carteles/fotos, 'slide' para presentaciones."
                    }
                },
                "required": ["prompt", "format"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "handle_customer_service",
            "description": "Gestiona problemas de postventa: devoluciones, quejas, estado de pedidos o reclamaciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_summary": {"type": "string", "description": "Resumen del problema del cliente."}
                },
                "required": ["issue_summary"]
            }
        }
    }
]
