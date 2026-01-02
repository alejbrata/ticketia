import os
import json
import io
import requests
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from flask import Flask, request, render_template, redirect, url_for, flash, send_file, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
import pandas as pd
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURACIÓN ---
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_super_secret_123'
    
    # Database Config (Postgres/SQLite)
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = 'sqlite:///instance/zeptai.db'
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)

# Inicializar Extensiones
db = SQLAlchemy(app)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Twilio Client (Opcional, para mensajes proactivos)
try:
    twilio_client = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
    twilio_sender = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
except:
    twilio_client = None

# --- MODELOS ---
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

# --- LÓGICA DE NEGOCIO (LOGIC.PY INTEGRADO) ---
def process_ticket_logic(media_url, user_phone):
    """
    1. Descarga imagen (si es necesario) o pasa URL.
    2. Consulta OpenAI.
    3. Guarda en DB.
    """
    try:
        # Prompt para GPT-4o
        prompt = f"""
        Actúa como experto contable español. Extrae datos de este ticket.
        HOY ES: {datetime.now().strftime('%d/%m/%Y')}.
        
        Devuelve JSON ESTRICTO:
        {{
            "fecha": "DD/MM/YYYY",
            "nif": "string",
            "proveedor": "string", 
            "numero_ticket": "string",
            "base": float,
            "iva_percent": float, 
            "cuota_iva": float,
            "total": float,
            "concepto": "resumen corto"
        }}
        Si falta algo, estima o pon null/0.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": media_url}}
                ]}
            ],
            max_tokens=300
        )
        
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # Guardar en DB
        new_ticket = Ticket(
            user_phone=user_phone,
            image_path=media_url, # En prod, subiríamos a S3 y guardaríamos esa URL
            status='processed',
            concept=data.get('concepto', 'Gasto Varios'),
            total=data.get('total', 0.0),
            date=datetime.strptime(data.get('fecha', datetime.now().strftime('%d/%m/%Y')), '%d/%m/%Y'),
            nif=data.get('nif'),
            provider=data.get('proveedor'),
            ticket_number=data.get('numero_ticket'),
            base=data.get('base', 0.0),
            tax_percent=data.get('iva_percent', 0.0),
            fee=data.get('cuota_iva', 0.0),
            raw_data=json.dumps(data)
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        
        return f"✅ Ticket de {data.get('proveedor')} guardado.\n💰 Total: {data.get('total')}€"
        
    except Exception as e:
        print(f"Error procesando ticket: {e}")
        return "⚠️ Error leyendo el ticket. Inténtalo de nuevo."

def generate_bot_response(user_msg, phone, profile):
    """Genera respuesta usando el System Prompt configurado."""
    if not profile or not profile.system_prompt:
        return "El asistente no está configurado."
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": profile.system_prompt},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error IA: {e}"

# --- RUTAS FLASK ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        user = BusinessProfile.query.filter_by(user_phone=phone).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_phone'] = user.user_phone
            session['business_name'] = user.business_name
            flash(f"Bienvenido {user.business_name}", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Credenciales incorrectas", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        business_name = request.form.get('business_name')
        
        if BusinessProfile.query.filter_by(user_phone=phone).first():
            flash("El teléfono ya está registrado", "error")
        else:
            new_user = BusinessProfile(
                user_phone=phone,
                password_hash=generate_password_hash(password),
                business_name=business_name,
                plan_tier='BASIC',
                features={"tickets_allowed": True, "bot_enabled": True}
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registro exitoso. Inicia sesión.", "success")
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_phone' not in session:
        return redirect(url_for('login'))
        
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    tickets = Ticket.query.filter_by(user_phone=session['user_phone']).order_by(Ticket.date.desc()).limit(10).all()
    
    # Calcular métricas simples
    total_gasto = sum(t.total or 0 for t in tickets)
    
    # Contexto para Template
    class UserContext:
        is_authenticated = True
        business_name = user.business_name
        bot_status = 'active' if user.system_prompt else 'inactive'
    
    return render_template('dashboard.html', 
                          current_user=UserContext(), 
                          tickets=tickets,
                          total_gastos=f"{total_gasto:.2f}")

@app.route('/wizard')
def wizard():
    if 'user_phone' not in session: return redirect(url_for('login'))
    
    class UserContext:
        is_authenticated = True
        
    return render_template('wizard.html', current_user=UserContext())

@app.route('/save_config', methods=['POST'])
def save_config():
    if 'user_phone' not in session: return redirect(url_for('login'))
    
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    form = request.form
    
    # Generar Prompt
    prompt = f"""
    Eres el asistente de {form.get('business_name')}.
    Sector: {form.get('sector')}.
    Tono: {form.get('tone')}.
    Servicios: {form.get('services')}.
    Horario: {form.get('schedule')}.
    """
    
    user.business_name = form.get('business_name')
    user.system_prompt = prompt
    db.session.commit()
    
    flash("Asistente Actualizado", "success")
    return redirect(url_for('dashboard'))

@app.route('/export_excel')
def export_excel():
    if 'user_phone' not in session: return redirect(url_for('login'))
    
    tickets = Ticket.query.filter_by(user_phone=session['user_phone']).all()
    
    data = []
    for t in tickets:
        data.append({
            "Fecha": t.date.strftime('%d/%m/%Y'),
            "Proveedor": t.provider,
            "Concepto": t.concept,
            "Base": t.base,
            "IVA": t.tax_percent,
            "Total": t.total,
            "Imagen": t.image_path
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Gastos')
        
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='gastos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/whatsapp', methods=['POST'])
def whatsapp_hook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    num_media = int(request.values.get('NumMedia', 0))
    
    resp = MessagingResponse()
    
    # 1. Identificar Usuario
    user = BusinessProfile.query.filter_by(user_phone=sender).first()
    
    if not user:
        resp.message("👋 Hola. No tienes cuenta en Zeptai. Regístrate en la web primero.")
        return str(resp)
        
    # 2. Lógica: Imagen vs Texto
    if num_media > 0:
        # Es un Ticket
        media_url = request.values.get('MediaUrl0')
        reply = process_ticket_logic(media_url, sender)
        resp.message(reply)
    else:
        # Es Chat (bot o comandos)
        if user.system_prompt:
            bot_reply = generate_bot_response(incoming_msg, sender, user)
            resp.message(bot_reply)
        else:
            resp.message("📸 Envíame una foto de un ticket para guardarlo.")
            
    return str(resp)

# Inicializar DB al arrancar si es main
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
