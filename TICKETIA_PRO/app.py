import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde el directorio padre
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
import io
import pandas as pd
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, session, jsonify, Response, stream_with_context
from flask_mail import Mail, Message
import secrets
from datetime import timedelta
from core.config import Config
from core.limiter import limiter
from core.db_models import db, BusinessProfile, Ticket, ChatMessage, Grant, Appointment, SynergyMatch, ActivityLog, GeneratedDocument, Notification, LLMCall
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from modules.tickets.logic import process_ticket_image
from modules.agents.manager import run_agent
from sqlalchemy.sql import func
from modules.services.notification import NotificationService

from werkzeug.security import generate_password_hash, check_password_hash
from core.logging_config import setup_logging

setup_logging()

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar Base de Datos
db.init_app(app)
mail = Mail(app)

# Rate limiting
limiter.init_app(app)

# --- GLOBAL CONTEXT PROCESSOR (NOTIFICACIONES) ---
@app.context_processor
def inject_notifications():
    if 'user_phone' in session:
        count = Notification.query.filter_by(
            user_phone=session['user_phone'], 
            is_read=False
        ).count()
        return dict(unread_notifications_count=count)
    return dict(unread_notifications_count=0)

# --- API NOTIFICACIONES ---
@app.route('/api/notifications')
def get_notifications():
    if 'user_phone' not in session: return jsonify([]), 401
    
    notifs = Notification.query.filter_by(user_phone=session['user_phone'])\
        .order_by(Notification.created_at.desc()).limit(20).all()
        
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "link": n.link,
        "is_read": n.is_read,
        "date": n.created_at.strftime('%d/%m %H:%M')
    } for n in notifs])

@app.route('/api/notifications/mark_read/<int:notif_id>', methods=['POST'])
def mark_notification_read(notif_id):
    if 'user_phone' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    n = db.session.get(Notification, notif_id)
    if n and n.user_phone == session['user_phone']:
        n.is_read = True
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    if 'user_phone' not in session: return jsonify({"error": "Unauthorized"}), 401

    Notification.query.filter_by(user_phone=session['user_phone'], is_read=False).update({Notification.is_read: True})
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/notifications/unread_count')
def notifications_unread_count():
    if 'user_phone' not in session: return jsonify({"count": 0}), 401
    count = Notification.query.filter_by(user_phone=session['user_phone'], is_read=False).count()
    return jsonify({"count": count})

# --- ADMIN PANEL CONFIGURATION ---
class SecureModelView(ModelView):
    """Clase base para proteger el panel de administración."""
    def is_accessible(self):
        # Solo permite acceso al email del 'Super Admin' (definido en seed_owner.py)
        # Ojo: Asegúrate de loguearte con este email.
        return session.get('user_email') == 'admin@ticketia.com'

    def inaccessible_callback(self, name, **kwargs):
        # Si no es admin, redirige al login
        flash('⚠️ Acceso restringido a administradores.', 'error')
        return redirect(url_for('web.login'))

# Inicializar el Panel
# Nota: template_mode='bootstrap4' puede requerir temas compatibles, si falla lo quitamos o usamos default
try:
    admin = Admin(app, name='Panel de Control Ticketia', template_mode='bootstrap4')
except TypeError:
    # Fallback si la versión instalada no soporta template_mode en init
    admin = Admin(app, name='Panel de Control Ticketia')

from flask_admin.menu import MenuLink
admin.add_link(MenuLink(name='🏠 Volver a Web', category='', url='/dashboard'))

# Añadir Vistas (Tablas visuales)
# 1. Gestión de Ayudas (Lo más importante para el Grant Hunter)
admin.add_view(SecureModelView(Grant, db.session, name='💰 Subvenciones'))

# 2. Gestión de Usuarios y Negocios
admin.add_view(SecureModelView(BusinessProfile, db.session, name='👥 Usuarios'))

# 3. Auditoría de Tickets
admin.add_view(SecureModelView(Ticket, db.session, name='🧾 Tickets'))

# 4. Logs del Chat y Citas
admin.add_view(SecureModelView(ChatMessage, db.session, name='💬 Chats'))
admin.add_view(SecureModelView(SynergyMatch, db.session, name='🤝 Matches'))
admin.add_view(SecureModelView(LLMCall, db.session, name='🧠 Métricas LLM'))
# admin.add_view(SecureModelView(Appointment, db.session, name='📅 Citas'))

with app.app_context():
    db.create_all()


# --- BLUEPRINTS REGISTRATION ---
from routes.web import web_bp
from routes.api import api_bp

app.register_blueprint(web_bp)
app.register_blueprint(api_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
