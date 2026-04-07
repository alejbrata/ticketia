import os
import io
import json
import secrets
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify, render_template, redirect, url_for, flash, send_file, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from core.db_models import BusinessProfile, Ticket, ChatMessage, GeneratedDocument, SynergyMatch, ActivityLog, db

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    if 'user_phone' in session:
        return redirect(url_for('web.dashboard'))
    return render_template('landing.html')

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        business_name = request.form.get('business_name', '').strip()

        # Validaciones básicas
        if not email or not phone or not password:
            flash('Por favor completa todos los campos.', 'error')
            return redirect(url_for('web.register'))

        # Check duplicados
        if BusinessProfile.query.filter((BusinessProfile.user_phone == phone) | (BusinessProfile.email == email)).first():
            flash('Este teléfono o email ya está registrado.', 'error')
            return redirect(url_for('web.register'))

        # Crear Usuario
        hashed_pw = generate_password_hash(password)
        new_user = BusinessProfile(
            user_phone=phone,
            email=email,
            password_hash=hashed_pw,
            business_name=business_name,
            plan_tier='BASIC', # Plan por defecto
            features={"tickets_allowed": True, "dashboard_access": True}
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Cuenta creada! Por favor inicia sesión.', 'success')
        return redirect(url_for('web.login'))

    return render_template('register.html')

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        # Buscar usuario por EMAIL
        profile = BusinessProfile.query.filter_by(email=email).first()
        
        if profile and check_password_hash(profile.password_hash, password):
            # Login exitoso
            session['user_phone'] = profile.user_phone # Mantenemos phone para logs y lógica
            session['user_email'] = profile.email
            session['business_name'] = profile.business_name
            flash(f'Bienvenido, {profile.business_name}', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('⚠️ Credenciales incorrectas.', 'error')
            
    return render_template('login.html')

@web_bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('web.login'))

@web_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = BusinessProfile.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            reset_url = url_for('web.reset_password', token=token, _external=True)
            
            msg = Message('Restablecer Contraseña - Ticketia',
                          sender=current_app.config['MAIL_DEFAULT_SENDER'],
                          recipients=[email])
            msg.body = f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}\n\nSi no solicitaste esto, ignora este correo.'
            
            try:
                from app import mail
                mail.send(msg)
                flash('Te hemos enviado un correo con instrucciones.', 'info')
            except Exception as e:
                print(f"Error enviando mail: {e}")
                flash('Error al enviar el correo. Contacta soporte.', 'error')
        else:
            # Por seguridad, no decimos si el email existe o no, o sí? 
            # UX estándar: "Si el correo existe, recibirás un mensaje."
            flash('Si el correo existe, recibirás instrucciones.', 'info')
            
        return redirect(url_for('web.login'))
        
    return render_template('forgot_password.html')

@web_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = BusinessProfile.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('El enlace es inválido o ha expirado.', 'error')
        return redirect(url_for('web.login'))
        
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if not password:
            flash('La contraseña no puede estar vacía.', 'error')
            return redirect(request.url)
            
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('¡Contraseña restablecida! Inicia sesión.', 'success')
        return redirect(url_for('web.login'))
        
    return render_template('reset_token.html')

@web_bp.route('/marketplace')
def marketplace():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    # Asegurar que active_agents sea una lista
    if user.active_agents is None:
        user.active_agents = []
        
    return render_template('marketplace.html', current_user=user)

@web_bp.route('/toggle_agent/<agent_id>', methods=['POST'])
def toggle_agent(agent_id):
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    current_agents = list(user.active_agents or []) # Copia explícita
    
    if agent_id in current_agents:
        current_agents.remove(agent_id)
        flash(f'Agente desactivado.', 'info')
    else:
        current_agents.append(agent_id)
        flash(f'¡Agente activado! 🚀', 'success')
        
    user.active_agents = current_agents
    # Forzar actualización en Postgres (detectar cambios en JSON)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(user, "active_agents")
    
    db.session.commit()
    return redirect(url_for('web.marketplace'))

@web_bp.route('/agent_config/<agent_id>')
def agent_config(agent_id):
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
    
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    
    # Obtener configuración actual del agente (o dict vacío)
    current_config = user.agent_config.get(agent_id, {}) if user.agent_config else {}
    
    # Nombres bonitos
    agent_names = {
        "post_sales_service": "Servicio Post-Venta",
        "grant_hunter": "Grant Hunter",
        "networker": "Networking Agent"
    }
    name = agent_names.get(agent_id, agent_id)

    return render_template('agent_config.html', agent_id=agent_id, agent_name=name, config=current_config)

@web_bp.route('/save_agent_config/<agent_id>', methods=['POST'])
def save_agent_config(agent_id):
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    
    # 1. Leer checkboxes (si no están, es False)
    enable_feedback = 'enable_feedback' in request.form
    enable_reactivation = 'enable_reactivation' in request.form
    # 1.5 Leer Ofertas
    offer_type = request.form.get('offer_type', '10% de Descuento')
    custom_offer_text = request.form.get('custom_offer_text', '')
    
    # 2. Actualizar JSON
    # Necesitamos copiar el dict completo para que SQLAlchemy detecte el cambio si anidamos
    full_config = dict(user.agent_config) if user.agent_config else {}
    
    # Actualizamos solo la key de este agente
    full_config[agent_id] = {
        "enable_feedback": enable_feedback,
        "enable_reactivation": enable_reactivation,
        "offer_type": offer_type,
        "custom_offer_text": custom_offer_text
    }
    
    user.agent_config = full_config
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(user, "agent_config")
    
    db.session.commit()
    
    flash('Configuración actualizada.', 'success')
    return redirect(url_for('web.marketplace'))

@web_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user_phone = session['user_phone']
    user = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    
    if request.method == 'POST':
        # Change Password Logic
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        
        if not check_password_hash(user.password_hash, current_password):
            flash('La contraseña actual es incorrecta.', 'error')
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Contraseña actualizada correctamente.', 'success')
            
    return render_template('profile.html', user=user)

@web_bp.route('/dashboard')
def dashboard():
    # 1. Protección de Ruta
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
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
    
    # B. Tickets Pendientes
    tickets_pendientes = Ticket.query.filter_by(
        user_phone=user_phone, 
        status='pending'
    ).count()

    # B2. Tickets Procesados
    tickets_procesados = Ticket.query.filter_by(
        user_phone=user_phone, 
        status='processed'
    ).count()
    
    # C. Chats Atendidos
    chats_atendidos = ChatMessage.query.filter_by(
        user_phone=user_phone, 
        role='user'
    ).count()

    # D. Activity Logs (NUEVO)
    recent_activity = ActivityLog.query.filter_by(user_phone=user_phone)\
        .order_by(ActivityLog.timestamp.desc())\
        .limit(10).all()
    
    # Nombre del mes
    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    month_name = meses_es.get(now.month, "Mes Actual")

    class UserContext:
        is_authenticated = True
        phone = user_phone
        business_name = profile.business_name if profile else "Mi Negocio"
        subscription_status = 'active' 
        has_bot = profile.features.get('bot_enabled', False) if profile and profile.features else False
        is_configured = True if (profile and profile.system_prompt) else False
        bot_status = 'active' if (has_bot and is_configured) else 'inactive' 
    
    # --- Date Helpers for UI ---
    from datetime import timedelta
    yesterday = now - timedelta(days=1)
    now_str = now.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')

    return render_template(
        'dashboard.html', 
        current_user=UserContext(), 
        tickets=tickets,
        total_gastos=total_gastos_fmt,
        tickets_pendientes=tickets_pendientes,
        tickets_procesados=tickets_procesados, # Fix syntax error from previous view? No, comma is fine
        chats_atendidos=chats_atendidos,
        current_month_name=month_name,
        logs=recent_activity,
        now_str=now_str,
        yesterday_str=yesterday_str
    )

@web_bp.route('/transactions')
def transactions():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user_phone = session['user_phone']
    
    # Traer TODOS los tickets
    tickets = Ticket.query.filter_by(user_phone=user_phone).order_by(Ticket.date.desc()).all()
    
    return render_template('transactions.html', tickets=tickets)

@web_bp.route('/documents')
def documents_page():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user_phone = session['user_phone']
    
    # Obtener documentos
    all_docs = GeneratedDocument.query.filter_by(user_phone=user_phone).order_by(GeneratedDocument.created_at.desc()).all()
    
    def group_by_date(docs):
        grouped = {}
        for doc in docs:
            year = doc.created_at.year
            month = doc.created_at.strftime('%B').capitalize() # Enero, Febrero... (depende de locale, por ahora usamos inglés o map)
            
            # Map simple de meses por si acaso el locale no está en ES
            months_es = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            month = months_es.get(doc.created_at.month, month)

            if year not in grouped: grouped[year] = {}
            if month not in grouped[year]: grouped[year][month] = []
            grouped[year][month].append(doc)
        return grouped

    # Categorizar y Agrupar
    docs_proposals = [d for d in all_docs if d.doc_type in ['proposal', 'invoice', 'report']]
    docs_images = [d for d in all_docs if d.doc_type == 'image']
    docs_presentations = [d for d in all_docs if d.doc_type == 'presentation']
    docs_video_prompts = [d for d in all_docs if d.doc_type == 'video_prompt']
    
    # Convertir a Árbol
    tree_proposals = group_by_date(docs_proposals)
    tree_images = group_by_date(docs_images)
    tree_presentations = group_by_date(docs_presentations)
    tree_videos = group_by_date(docs_video_prompts)
    
    # --- Mobile UX helpers ---
    from datetime import timedelta
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    now_str = now.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    return render_template('documents.html', 
                           tree_proposals=tree_proposals, 
                           tree_images=tree_images, 
                           tree_presentations=tree_presentations,
                           tree_videos=tree_videos,
                           # Pasamos contadores para los badges
                           count_proposals=len(docs_proposals),
                           count_images=len(docs_images),
                           count_presentations=len(docs_presentations),
                           count_videos=len(docs_video_prompts),
                           now_str=now_str,
                           yesterday_str=yesterday_str)

@web_bp.route('/delete_document/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    if 'user_phone' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    doc = GeneratedDocument.query.get(doc_id)
    if not doc:
        return jsonify({"success": False, "error": "Document not found"}), 404
        
    if doc.user_phone != session['user_phone']:
        return jsonify({"success": False, "error": "Forbidden"}), 403
        
    try:
        # 1. Borrar archivo físico
        try:
            # doc.file_path es relativo: /static/generated_docs/file.pdf
            # Convertir a absoluto
            relative_path = doc.file_path.lstrip('/')
            absolute_path = os.path.join(current_app.root_path, relative_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
        except Exception as e:
            print(f"Error borrando archivo físico {doc.file_path}: {e}")
            # Continuamos para borrar de DB aunque falle disco
            
        # 2. Borrar de DB
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@web_bp.route('/wizard')
def wizard():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
    user_phone = session['user_phone']
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    
    # Si no existe perfil, pasar un objeto vacío o usar valores por defecto
    if not profile:
        class MockProfile:
            business_name = ""
            static_knowledge = {}
            logo_path = None
        profile = MockProfile()
        
    return render_template('wizard.html', current_user=profile)

@web_bp.route('/save_config', methods=['POST'])
def save_config():
    # 1. Auth Real (Protección)
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
        
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
    
    # 3.5 Guardar Logo si existe
    logo_path = None
    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"logo_{user_phone}_{file.filename}")
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            logo_path = f"/static/uploads/logos/{filename}"
    
    # 4. Guardar en Base de Datos
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    
    static_data = {
        "sector": sector,
        "tone": tone, # Guardar tono también
        "schedule": schedule,
        "payment_methods": payment_methods,
        "services": services,
        "instructions": instructions # Guardar instrucciones para rellenar
    }
    
    if profile:
        # Actualizar existente
        profile.business_name = b_name
        profile.system_prompt = generated_system_prompt.strip()
        profile.static_knowledge = static_data
        if logo_path:
            profile.logo_path = logo_path
    else:
        # Crear nuevo
        new_profile = BusinessProfile(
            user_phone=user_phone,
            business_name=b_name,
            system_prompt=generated_system_prompt.strip(),
            static_knowledge=static_data,
            logo_path=logo_path
        )
        db.session.add(new_profile)
    
    db.session.commit()
    
    flash('¡Configuración guardada y Agente IA actualizado!', 'success')
    return redirect(url_for('web.dashboard'))

@web_bp.route('/agents')
def agents_page():
    if 'user_phone' not in session:
        return redirect(url_for('web.login'))
    return render_template('agents.html')

@web_bp.route('/export_excel')
def export_excel():
    # 1. Protección de Ruta
    if 'user_phone' not in session:
        flash('Debes iniciar sesión para exportar tus gastos.', 'error')
        return redirect(url_for('web.login'))
        
    user_phone = session['user_phone']
    
    # Recuperar perfil para el nombre del archivo
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    business_name = profile.business_name if profile and profile.business_name else f"Zeptai_{user_phone}"

    # 2. Query a Base de Datos (Filtrado por usuario)
    tickets = Ticket.query.filter_by(user_phone=user_phone).order_by(Ticket.date.desc()).all()
    
    if not tickets:
        flash('No hay tickets para exportar.', 'warning')
        return redirect(url_for('web.dashboard'))
    
    # 3. Preparar Datos para DataFrame
    data_list = []
    base_url = request.host_url.rstrip('/') 
    urls = [] # Lista auxiliar para guardar las URLs
    
    for t in tickets:
        # Calcular Cuota IVA (Fee) si falta
        fee = t.fee
        if (fee is None or fee == 0) and t.base and t.tax_percent:
             fee = t.base * (t.tax_percent / 100)
             
        # Construir URL de imagen
        full_img_url = ""
        if t.image_path:
            if t.image_path.startswith(('http://', 'https://')):
                full_img_url = t.image_path
            else:
                full_img_url = f"{base_url}{t.image_path}"
        
        urls.append(full_img_url)

        data_list.append({
            "ID": t.id,
            "Date": t.date,
            "Month": t.date.month if t.date else None,
            "Year": t.date.year if t.date else None,
            "NIF": t.nif,
            "Name": t.provider, # Mapeado desde provider
            "Ticket_Number": t.ticket_number,
            "Concept": t.concept,
            "Expense_Account": "629", # Valor fijo
            "Base": t.base,
            "%IVA": t.tax_percent,
            "Fee": fee,
            "Total": t.total,
            "Enlace Imagen": "Ver Recibo" if full_img_url else ""
        })
        
    # 4. Crear DataFrame y Excel con XlsxWriter
    column_order = ["ID", "Date", "Month", "Year", "NIF", "Name", "Ticket_Number", "Concept", "Expense_Account", "Base", "%IVA", "Fee", "Total", "Enlace Imagen"]
    
    df = pd.DataFrame(data_list)
    # Asegurarse que todas las columnas existan
    for col in column_order:
        if col not in df.columns:
            df[col] = None
            
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
        # ID (A)
        worksheet.set_column('A:A', 8, center_format)
        # Date (B)
        worksheet.set_column('B:B', 12, date_format)
        # Month (C)
        worksheet.set_column('C:C', 6, center_format)
        # Year (D)
        worksheet.set_column('D:D', 6, center_format)
        # NIF (E)
        worksheet.set_column('E:E', 12, center_format)
        # Name (F) - Provider
        worksheet.set_column('F:F', 25)
        # Ticket_Number (G)
        worksheet.set_column('G:G', 15, center_format)
        # Concept (H)
        worksheet.set_column('H:H', 30)
        # Expense_Account (I)
        worksheet.set_column('I:I', 10, center_format)
        # Base (J)
        worksheet.set_column('J:J', 12, currency_format)
        # %IVA (K)
        worksheet.set_column('K:K', 8, center_format)
        # Fee (L)
        worksheet.set_column('L:L', 12, currency_format)
        # Total (M)
        worksheet.set_column('M:M', 15, currency_format)
        # Enlace (N)
        worksheet.set_column('N:N', 15, center_format)

        # Sobreescribir Cabeceras con Estilo
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Re-escribir enlaces
        link_col_idx = 13 # Columna N (0-based index 13)
        for i, url in enumerate(urls):
            if url:
                worksheet.write_url(i + 1, link_col_idx, url, link_format, string="Ver Recibo")
        
    output.seek(0)
    
    # Nombre de archivo dinámico (Con TIMESTAMP para cache busting)
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9]', '', business_name)
    date_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    filename = f"Gastos_{safe_name}_{date_str}.xlsx"
    
    print(f"Generando Excel: {filename}") # Debug Log
    
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- WEBHOOK WHATSAPP (Backend Logic) ---

@web_bp.route('/demo')
def demo_panel():
    if 'user_phone' not in session: return redirect(url_for('web.login'))
    return render_template('demo_panel.html')

@web_bp.route('/demo/seed_data', methods=['POST'])
def demo_seed():
    from seed_demo import generate_fake_history
    generate_fake_history(session['user_phone'])
    flash('✅ Datos históricos inyectados.', 'success')
    return redirect(url_for('web.demo_panel'))

@web_bp.route('/demo/trigger/<agent_name>', methods=['POST'])
def demo_trigger(agent_name):
    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    try:
        if agent_name == 'coach':
            from modules.proactive.business_health import BusinessCoachAgent
            BusinessCoachAgent().run_daily_analysis(user)
        elif agent_name == 'hunter':
            from modules.proactive.grant_hunter import GrantHunterAgent
            GrantHunterAgent().check_new_grants(user)
        elif agent_name == 'networker':
            from modules.proactive.networker import SynergyAgent
            SynergyAgent().run_daily_networking(user)
        flash(f'🚀 Agente {agent_name} ejecutado con éxito.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('web.demo_panel'))

@web_bp.route('/setup_magic_db_force')
def setup_magic_db():
    # PROTECTED ROUTE (Dev Only)
    secret_key = request.args.get('key')
    if secret_key != os.environ.get('DEV_SECRET_KEY', 'super_secret_dev_key'): # Default fallback strict
        return "<h1>⛔ Acceso Denegado</h1>", 403

    try:
        # Importamos aquí para evitar ciclos
        from reset_db_full import reset_and_seed
        
        # Ejecutamos el script que borra y crea todo
        reset_and_seed()
        
        return """
        <div style="font-family: sans-serif; padding: 2rem; text-align: center;">
            <h1 style="color: green;">✅ Instalación Completada</h1>
            <p>La base de datos se ha reiniciado y el usuario Admin ha sido restaurado.</p>
            <div style="background: #f0f0f0; padding: 1rem; display: inline-block; border-radius: 8px; text-align: left;">
                <p><strong>Usuario:</strong> 34630339601</p>
                <p><strong>Contraseña:</strong> 1234</p>
            </div>
            <br><br>
            <a href="/login" style="background: blue; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Ir al Login</a>
        </div>
        """
    except Exception as e:
        return f"<h1 style='color: red'>❌ Error: {str(e)}</h1>"
# ---------------------------------------------------------------        

# --- THE COUNCIL ROUTES ---
@web_bp.route('/council')
def council_page():
    if not session.get('user_phone'):
        return redirect(url_for('web.login'))
    return render_template('council.html', current_page='council')


