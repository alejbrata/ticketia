from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BusinessProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(20), unique=False, nullable=False) # Phone still mandatory for bot, but not primary login
    email = db.Column(db.String(120), unique=True, nullable=False) # New Login ID
    business_name = db.Column(db.String(100))
    logo_path = db.Column(db.String(300)) # Logo URL for PPTX/Web
    password_hash = db.Column(db.String(200)) # Auth
    
    # Password Recovery
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # SaaS Info
    plan_tier = db.Column(db.String(20), default='BASIC')
    whatsapp_number = db.Column(db.String(20)) # Número asignado (si aplica)
    twilio_sid = db.Column(db.String(50))
    features = db.Column(db.JSON, default={}) # {"bot_enabled": true}
    
    # Chatbot Config
    system_prompt = db.Column(db.Text)
    static_knowledge = db.Column(db.JSON, default={})
    
    # Marketplace (Suscripciones a Agentes)
    # Lista de IDs de agentes activos ej: ["grant_hunter", "networker"]
    active_agents = db.Column(db.JSON, default=[])
    # Configuración específica de cada agente ej: {"post_sales_service": {"ask_feedback": True}}
    agent_config = db.Column(db.JSON, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(20), nullable=False)
    image_path = db.Column(db.String(300)) # URL o Path en Drive/S3
    status = db.Column(db.String(20), default='pending') # pending, processed
    
    # Datos Fiscales
    concept = db.Column(db.String(100))
    total = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Detalles Avanzados
    nif = db.Column(db.String(20))
    provider = db.Column(db.String(100))
    ticket_number = db.Column(db.String(50))
    base = db.Column(db.Float)
    tax_percent = db.Column(db.Float)
    fee = db.Column(db.Float)
    
    raw_data = db.Column(db.Text) # JSON respaldo

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_phone = db.Column(db.String(20), nullable=False) # Dueño del calendario
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    time = db.Column(db.String(10), nullable=False) # HH:MM
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(20), nullable=False, index=True) # Vinculado al cliente
    role = db.Column(db.String(20), nullable=False) # 'user', 'assistant', 'tool'
    content = db.Column(db.Text)
    tool_call_id = db.Column(db.String(100), nullable=True) # Para enlazar respuestas de tools
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sector_focus = db.Column(db.String(100)) # Ej: "Hostelería", "Tech", "General"
    amount = db.Column(db.String(50)) # Ej: "Hasta 2.000€"
    link = db.Column(db.String(300))
    deadline = db.Column(db.String(50))
    # Lista de teléfonos notificados (JSON) para evitar spam
    notified_phones = db.Column(db.JSON, default=[]) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SynergyMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_a_phone = db.Column(db.String(20), nullable=False) # Quien recibe la sugerencia
    user_b_phone = db.Column(db.String(20), nullable=False) # El candidato sugerido
    score = db.Column(db.Integer) # 0-100 Puntuación de la IA
    reason = db.Column(db.Text)   # Por qué hacen buena pareja
    status = db.Column(db.String(20), default='suggested') # suggested, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
