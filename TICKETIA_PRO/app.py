import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio padre
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
import io
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, session
from twilio.twiml.messaging_response import MessagingResponse

from core.config import Config
from core.db_models import db, BusinessProfile, Ticket
from modules.tickets.logic import process_ticket
from modules.chatbot.logic import generate_response
from sqlalchemy.sql import func

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar Base de Datos
db.init_app(app)

with app.app_context():
    db.create_all()

# --- RUTAS WEB (Frontend) ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        business_name = request.form.get('business_name', '').strip()

        # Validaciones básicas
        if not phone or not password:
            flash('Por favor completa todos los campos.', 'error')
            return redirect(url_for('register'))

        # Check duplicados
        if BusinessProfile.query.filter_by(user_phone=phone).first():
            flash('Este teléfono ya está registrado.', 'error')
            return redirect(url_for('register'))

        # Crear Usuario
        hashed_pw = generate_password_hash(password)
        new_user = BusinessProfile(
            user_phone=phone,
            password_hash=hashed_pw,
            business_name=business_name,
            plan_tier='BASIC', # Plan por defecto
            features={"tickets_allowed": True, "dashboard_access": True}
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Cuenta creada! Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        # Buscar usuario
        profile = BusinessProfile.query.filter_by(user_phone=phone).first()
        
        if profile and check_password_hash(profile.password_hash, password):
            # Login exitoso
            session['user_phone'] = profile.user_phone
            session['business_name'] = profile.business_name
            flash(f'Bienvenido, {profile.business_name}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('⚠️ Credenciales incorrectas.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    # 1. Protección de Ruta
    if 'user_phone' not in session:
        return redirect(url_for('login'))
        
    user_phone = session['user_phone']
    
    # 2. Obtener Datos Reales
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    # Limitamos a 5 para el dashboard
    tickets = Ticket.query.filter_by(user_phone=user_phone).order_by(Ticket.date.desc()).limit(5).all()
    # Para calcular contadores, necesitamos TODOS los tickets (o hacer queries count separadas)
    # Haremos queries separadas para contadores abajo para no traer todo a memoria en dashboard

    
    # --- MÉTRICAS ---
    # A. Total Gastos Mes Actual (SQLAlchemy Robusto)
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1).date()
    
    total_gastos = db.session.query(func.sum(Ticket.total)).filter(
        Ticket.user_phone == user_phone,
        Ticket.date >= month_start
    ).scalar() or 0.0
    
    # Formatear bonito (ej: 1.250,50)
    total_gastos_fmt = f"{total_gastos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    
    # B. Tickets Pendientes (SQL Count directo)
    tickets_pendientes = Ticket.query.filter_by(
        user_phone=user_phone, 
        status='pending'
    ).count()

    # B2. Tickets Procesados (SQL Count directo)
    tickets_procesados = Ticket.query.filter_by(
        user_phone=user_phone, 
        status='processed'
    ).count()
    
    # C. Chats Atendidos (Placeholder por ahora, ya que no guardamos logs de chat persistentes en DB aún)
    chats_atendidos = 0
    
    class UserContext:
        is_authenticated = True
        phone = user_phone
        business_name = profile.business_name if profile else "Mi Negocio"
        # Pasamos el estado de suscripción real también si existe en User, pero aquí usamos profile
        # Vamos a asumir 'active' o leer de User. Por simplicidad en MVP:
        subscription_status = 'active' 
        # Bot Logic
        has_bot = profile.features.get('bot_enabled', False) if profile and profile.features else False
        is_configured = True if (profile and profile.system_prompt) else False
        bot_status = 'active' if (has_bot and is_configured) else 'inactive' 
    
    return render_template(
        'dashboard.html', 
        current_user=UserContext(), 
        tickets=tickets,
        total_gastos=total_gastos_fmt,
        tickets_pendientes=tickets_pendientes,
        tickets_procesados=tickets_procesados,
        chats_atendidos=chats_atendidos
    )

@app.route('/transactions')
def transactions():
    if 'user_phone' not in session:
        return redirect(url_for('login'))
        
    user_phone = session['user_phone']
    
    # Traer TODOS los tickets
    tickets = Ticket.query.filter_by(user_phone=user_phone).order_by(Ticket.date.desc()).all()
    
    return render_template('transactions.html', tickets=tickets)

@app.route('/wizard')
def wizard():
    # Mock user for Authentication
    class MockUser:
        phone = "+34600123456"
        subscription_status = "active"
        is_authenticated = True
    
    return render_template('wizard.html', current_user=MockUser())

@app.route('/save_config', methods=['POST'])
@app.route('/save_config', methods=['POST'])
def save_config():
    # 1. Auth Real (Protección)
    if 'user_phone' not in session:
        return redirect(url_for('login'))
        
    user_phone = session['user_phone']
    
    # 2. Recuperar datos del formulario
    data = request.form
    b_name = data.get('business_name')
    sector = data.get('sector')
    tone = data.get('tone')
    schedule = data.get('schedule')
    payment_methods = data.get('payment_methods')
    services = data.get('services')
    instructions = data.get('business_instructions', '')
    
    # 3. Lógica: Construir System Prompt
    generated_system_prompt = f"""
    Eres el asistente virtual de {b_name}, un negocio del sector {sector}.
    Tu tono debe ser {tone}.
    
    INFORMACIÓN CLAVE:
    - Horario: {schedule}
    - Pagos aceptados: {payment_methods}
    - Servicios principales: {services}
    
    INSTRUCCIONES EXTRA:
    {instructions}
    
    OBJETIVO:
    Responde a las dudas de los clientes basándote ÚNICAMENTE en esta información.
    Si te preguntan algo que no sabes, pide amablemente que contacten por teléfono.
    """
    
    # 4. Guardar en Base de Datos
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    
    static_data = {
        "sector": sector,
        "schedule": schedule,
        "payment_methods": payment_methods,
        "services": services
    }
    
    if profile:
        # Actualizar existente
        profile.business_name = b_name
        profile.system_prompt = generated_system_prompt.strip()
        profile.static_knowledge = static_data
    else:
        # Crear nuevo
        new_profile = BusinessProfile(
            user_phone=user_phone,
            business_name=b_name,
            system_prompt=generated_system_prompt.strip(),
            static_knowledge=static_data
        )
        db.session.add(new_profile)
    
    db.session.commit()
    
    flash('¡Configuración guardada y Agente IA actualizado!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/export_excel')
def export_excel():
    # 1. Protección de Ruta
    if 'user_phone' not in session:
        flash('Debes iniciar sesión para exportar tus gastos.', 'error')
        return redirect(url_for('login'))
        
    user_phone = session['user_phone']
    
    # Recuperar perfil para el nombre del archivo
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    business_name = profile.business_name if profile and profile.business_name else f"Zeptai_{user_phone}"

    # 2. Query a Base de Datos (Filtrado por usuario)
    tickets = Ticket.query.filter_by(user_phone=user_phone).order_by(Ticket.date.desc()).all()
    
    if not tickets:
        flash('No hay tickets para exportar.', 'warning')
        return redirect(url_for('dashboard'))
    
    # 3. Preparar Datos para DataFrame
    data_list = []
    base_url = request.host_url.rstrip('/') 
    
    # Lista auxiliar para guardar las URLs
    urls = []
    
    for t in tickets:
        if t.image_path and t.image_path.startswith(('http://', 'https://')):
            full_img_url = t.image_path
        else:
            full_img_url = f"{base_url}{t.image_path}" if t.image_path else ""
        
        urls.append(full_img_url)
        
        # Cálculos Económicos
        total = float(t.total or 0.0)
        tax_rate = float(t.tax_percent or 21.0) # Usar el IVA guardado
        
        # Base = Total / (1 + tasa/100)
        base_imponible = round(total / (1 + (tax_rate / 100)), 2)
        cuota_iva = round(total - base_imponible, 2)
        
        data_list.append({
            "Fecha": t.date,
            "ID Ref": t.id,
            "Cuenta Contable": "41000000", # Contaplus Placeholder
            "Concepto": t.concept or "Gasto General",
            "Base Imponible": base_imponible,
            "% IVA": tax_rate,
            "Cuota IVA": cuota_iva,
            "Total Factura": total,
            "Enlace Imagen": "Ver Recibo"
        })
        
    # 4. Crear DataFrame y Excel con XlsxWriter
    column_order = ['Fecha', 'ID Ref', 'Cuenta Contable', 'Concepto', 
                   'Base Imponible', '% IVA', 'Cuota IVA', 'Total Factura', 'Enlace Imagen']
    
    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df[column_order]
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sheet_name = 'Gastos'
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # --- ESTILOS ---
        
        # 1. Cabecera (Azul Oscuro, Negrita, Blanco)
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#1f4e78', # Business Blue
            'font_color': '#ffffff',
            'border': 1
        })
        
        # 2. Moneda (€)
        currency_format = workbook.add_format({'num_format': '#,##0.00 "€"'})
        
        # 3. Fecha Centrada
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
        
        # 4. Centro
        center_format = workbook.add_format({'align': 'center'})
        
        # 5. Enlaces
        link_format = workbook.add_format({'font_color': 'blue', 'underline': 1})
        
        # Aplicar formato a columnas (0-index based)
        # A: Fecha
        worksheet.set_column('A:A', 12, date_format)
        # B: ID Ref
        worksheet.set_column('B:B', 8, center_format)
        # C: Cuenta
        worksheet.set_column('C:C', 15, center_format)
        # D: Concepto (Ancho flexible)
        worksheet.set_column('D:D', 35)
        # E: Base Imponible
        worksheet.set_column('E:E', 15, currency_format)
        # F: % IVA
        worksheet.set_column('F:F', 8, center_format)
        # G: Cuota IVA
        worksheet.set_column('G:G', 12, currency_format)
        # H: Total
        worksheet.set_column('H:H', 15, currency_format)
        # I: Enlace
        worksheet.set_column('I:I', 15)

        # Sobreescribir Cabeceras con Estilo
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Re-escribir enlaces
        link_col_idx = 8 
        for i, url in enumerate(urls):
            if url:
                worksheet.write_url(i + 1, link_col_idx, url, link_format, string="Ver Recibo")
        
    output.seek(0)
    
    # Nombre de archivo dinámico y limpio
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9]', '', business_name) # Remove special chars
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"Gastos_{safe_name}_{date_str}.xlsx"
    
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- WEBHOOK WHATSAPP (Backend Logic) ---

@app.route('/voice/reject', methods=['POST'])
def reject_voice():
    """Endpoint para rechazar llamadas de voz en números de solo-texto/bot."""
    from twilio.twiml.voice_response import VoiceResponse
    resp = VoiceResponse()
    resp.reject(reason='busy')
    return str(resp)

@app.route('/whatsapp', methods=['POST'])
def bot():
    """
    Router V2: Lógica Multi-Tenant Estricta
    distingue entre Número Central (Ticketia) y Números Dedicados (Clientes).
    """
    
    # 1. Obtener datos y limpiar números
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    target_number = request.values.get('To', '').replace('whatsapp:', '') # A quién escriben
    num_media = int(request.values.get('NumMedia', 0))
    
    resp = MessagingResponse()
    
    # --- CONSTANTES ---
    CENTRAL_NUMBER_ID = os.environ.get('CENTRAL_WHATSAPP_NUMBER', 'ticketia_central') 
    # (En producción esto debería ser el número real de Twilio de la plataforma)
    
    # 2. ENRUTAMIENTO
    
    # A) ¿Están escribiendo al NÚMERO CENTRAL?
    # (Asumimos que si no matchea con un cliente dedicado, es central, o chequeamos un ID fijo)
    # Para este MVP, verificaremos si el target_number coincide con algún cliente.
    
    target_business = BusinessProfile.query.filter_by(whatsapp_number=target_number).first()
    
    if not target_business:
        # => CASO 1: Escriben a TICKETIA CENTRAL (o número desconocido)
        # Lógica: Solo permitimos subir tickets a usuarios registrados.
        
        user_profile = BusinessProfile.query.filter_by(user_phone=sender).first()
        
        if user_profile:
            # Es un usuario (Dueño) hablando con la central
            if num_media > 0:
                # Chequeo de Plan (Features)
                features = user_profile.features or {}
                if features.get('can_upload_tickets', True):
                    media_url = request.values.get('MediaUrl0')
                    logic_response = process_ticket(media_url, sender)
                    resp.message(logic_response)
                else:
                    resp.message("⛔ Tu plan actual no incluye gestión de tickets.")
            else:
                resp.message(f"Hola {user_profile.business_name}. Envíame una foto del ticket para procesarlo. 📸")
        else:
            # Usuario NO registrado
            resp.message("🤖 Bienvenido a Zeptai. Para usar este bot de gastos, por favor regístrate en nuestra web.")
            
    else:
        # => CASO 2: Escriben a un NÚMERO DEDICADO DE CLIENTE
        # target_business es la empresa a la que quieren contactar
        
        # ¿Quién escribe?
        if sender == target_business.user_phone:
            # A.1) ES EL DUEÑO probando su propio bot
            if num_media > 0:
                 # Si el dueño se manda foto a su propio bot de cliente -> ¿Lo procesamos como ticket?
                 # Generalmente NO, el bot de cliente es para clientes. 
                 # Pero si su plan lo permite, podríamos.
                 # Por simplicidad: Los tickets se suben al CENTRAL. Aquí asumimos test del bot.
                 resp.message("⚠️ Estás hablando con TU bot de atención al cliente (Modo Test). Para subir gastos, escribe al número Central de Zeptai.")
            else:
                 # Responder como simulación de bot
                 try:
                    ai_response = generate_response(incoming_msg, target_number)
                    resp.message(f"[TEST MODO DUEÑO] 🤖: {ai_response}")
                 except Exception as e:
                    resp.message(f"Error Test: {e}")
        else:
            # A.2) ES UN CLIENTE FINAL
            # Verificar si el plan incluye Chatbot
            features = target_business.features or {}
            if features.get('has_chatbot', False):
                try:
                    ai_response = generate_response(incoming_msg, target_number)
                    resp.message(ai_response)
                except Exception as e:
                    print(f"Error Chatbot V2: {e}")
                    # Silencio o error genérico en logs
            else:
                # El negocio tiene número pero no bot contratado (Raro)
                pass 

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Puerto 5001 para no chocar con el otro bot
