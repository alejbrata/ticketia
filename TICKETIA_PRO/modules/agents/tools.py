import json
from core.db_models import db, Appointment

class CalendarTools:
    """Clase utilitaria que simula herramientas de calendario."""

    @staticmethod
    def check_availability(date: str, business_phone: str) -> str:
        """
        Consulta disponibilidad real en base de datos.
        """
        print(f"🛠️ [TOOL CALL] check_availability(date='{date}', business='{business_phone}')")
        
        # 1. Definir Slots Fijos (Simplificación MVP)
        # Asumimos que todos los negocios abren de 09:00 a 18:00
        all_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "16:00", "17:00", "18:00"]
        
        # 2. Consultar Citas Existentes para ese día y negocio
        # (Nota: date debe venir como YYYY-MM-DD string)
        existing_appointments = Appointment.query.filter_by(
            business_phone=business_phone,
            date=date
        ).all()
        
        busy_times = [appt.time for appt in existing_appointments]
        
        # 3. Calcular Huecos Libres
        available_slots = [slot for slot in all_slots if slot not in busy_times]
        
        if not available_slots:
            return "Lo siento, no quedan huecos disponibles para esa fecha."
            
        return f"Huecos disponibles: {', '.join(available_slots)}"

    @staticmethod
    def book_appointment(date: str, time: str, client_name: str, phone: str, business_phone: str) -> str:
        """
        Reserva una cita real en la base de datos.
        """
        print(f"🛠️ [TOOL CALL] book_appointment(date='{date}', time='{time}', client='{client_name}')")
        
        # 1. Verificar si ya está ocupado (Doble check)
        existing = Appointment.query.filter_by(
            business_phone=business_phone,
            date=date,
            time=time
        ).first()
        
        if existing:
            return f"❌ Lo siento, el horario de las {time} ya está ocupado. Por favor elige otro."
            
        # 2. Crear Cita
        new_appt = Appointment(
            business_phone=business_phone,
            date=date,
            time=time,
            client_name=client_name,
            client_phone=phone
        )
        
        try:
            db.session.add(new_appt)
            db.session.commit()
            return f"✅ Cita confirmada para el {date} a las {time}. ¡Te esperamos, {client_name}!"
        except Exception as e:
            print(f"Error DB: {e}")
            return "⚠️ Hubo un error al guardar tu cita. Por favor intenta más tarde."

# Definición del esquema para OpenAI (Function Calling)
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
                        "description": "La fecha para consultar disponibilidad (Formato exacto: YYYY-MM-DD)."
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
                    "date": {
                        "type": "string",
                        "description": "Fecha de la cita (YYYY-MM-DD)."
                    },
                    "time": {
                        "type": "string",
                        "description": "Hora de la cita (ej: 10:00)."
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Nombre del cliente."
                    },
                    "phone": {
                        "type": "string",
                        "description": "Teléfono de contacto del cliente."
                    }
                },
                "required": ["date", "time", "client_name", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_proposal_from_last_image",
            "description": "Utiliza la última imagen subida por el usuario (nota manuscrita o servilleta) para redactar un presupuesto formal en PDF.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_proposal_from_text",
            "description": "Genera un presupuesto PDF formal directamente desde los datos proporcionados por texto/voz (sin imagen).",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Nombre del cliente."},
                    "items": {
                        "type": "array",
                        "description": "Lista de items/servicios.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "desc": {"type": "string", "description": "Descripción del servicio/producto"},
                                "qty": {"type": "integer", "description": "Cantidad"},
                                "price": {"type": "number", "description": "Precio unitario"},
                                "total": {"type": "number", "description": "Total de línea"}
                            }
                        }
                    },
                    "total": {"type": "number", "description": "Total del presupuesto."},
                    "notes": {"type": "string", "description": "Notas adicionales o pie de página."}
                },
                "required": ["client_name", "items", "total"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_marketing_material",
            "description": "Crea material visual de marketing (imágenes publicitarias o diapositivas PPT) basado en una descripción o idea.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "La idea o descripción del contenido a generar."
                    },
                    "format": {
                        "type": "string",
                        "enum": ["image", "slide"],
                        "description": "Usa 'image' para carteles/fotos o 'slide' para presentaciones."
                    }
                },
                "required": ["prompt", "format"]
            }
        }
    }
]
