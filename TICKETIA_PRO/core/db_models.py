from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BusinessProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_phone = db.Column(db.String(20), unique=True, nullable=False)
    business_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(200)) # Auth
    
    # SaaS Info
    plan_tier = db.Column(db.String(20), default='BASIC')
    whatsapp_number = db.Column(db.String(20)) # Número asignado (si aplica)
    twilio_sid = db.Column(db.String(50))
    features = db.Column(db.JSON, default={}) # {"bot_enabled": true}
    
    # Chatbot Config
    system_prompt = db.Column(db.Text)
    static_knowledge = db.Column(db.JSON, default={})
    
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
