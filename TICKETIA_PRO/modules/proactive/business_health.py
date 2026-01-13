import os
import matplotlib
matplotlib.use('Agg') # Backend sin interfaz gráfica
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from twilio.rest import Client
from openai import OpenAI
from core.db_models import db, Ticket

class BusinessCoachAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.twilio = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        self.whatsapp_from = "whatsapp:+14155238886"

    def run_daily_analysis(self, user):
        """
        Analiza la salud financiera y envía feedback.
        """
        print(f"🩺 Coach: Analizando finanzas de {user.business_name}...")
        
        # 1. Obtener Datos (Mes Actual vs Mes Pasado)
        stats = self._get_financial_stats(user.user_phone)
        
        # Si no hay datos suficientes, no decimos nada aún (o para demo, sí)
        if stats['current_month'] == 0 and stats['last_month_mtd'] == 0:
            print("   -> Sin datos suficientes.")
            return

        # 2. Generar Mensaje + Gráfico
        message = self._generate_coach_message(user.business_name, stats)
        chart_url = self._generate_chart(user, stats)
        
        # 3. Enviar WhatsApp Multimodal
        if message:
            self._send_whatsapp_with_media(user.user_phone, message, chart_url)

    def _get_financial_stats(self, phone):
        today = datetime.now()
        start_current = today.replace(day=1, hour=0, minute=0, second=0)
        
        # Mes pasado completo (para referencia) o MTD (Month to Date)?
        # Mejor MTD: Comparar los primeros X días de este mes vs primeros X días del mes pasado.
        start_last = (start_current - relativedelta(months=1))
        # Para evitar problemas con días que no existen (ej: 31 feb), usar min() o lógica segura
        try:
             end_last_comparable = start_last + timedelta(days=today.day) # Mismo día del mes pasado
        except:
             end_last_comparable = start_last + relativedelta(day=31) # Fin de mes

        # Gastos Mes Actual
        current_total = db.session.query(func.sum(Ticket.total)).filter(
            Ticket.user_phone == phone,
            Ticket.date >= start_current
        ).scalar() or 0.0

        # Gastos Mes Pasado (mismo periodo)
        last_total = db.session.query(func.sum(Ticket.total)).filter(
            Ticket.user_phone == phone,
            Ticket.date >= start_last,
            Ticket.date < end_last_comparable
        ).scalar() or 0.0
        
        # Calcular tendencia
        diff_percent = 0
        if last_total > 0:
            diff_percent = ((current_total - last_total) / last_total) * 100
            
        return {
            "current_month": round(current_total, 2),
            "last_month_mtd": round(last_total, 2),
            "diff_percent": round(diff_percent, 1)
        }

    def _generate_coach_message(self, name, stats):
        prompt = f"""
        Eres un Coach Financiero personal para un autónomo llamado {name}.
        Datos financieros a fecha de hoy (comparado con el mes pasado a estas alturas):
        - Gasto Actual: {stats['current_month']}€
        - Gasto Mes Pasado: {stats['last_month_mtd']}€
        - Variación: {stats['diff_percent']}%

        Escribe un mensaje de WhatsApp CORTO y MOTIVADOR (máx 2 frases).
        - Si ha gastado MENOS: Celebra.
        - Si ha gastado MÁS: Alerta Constructiva.
        
        Tono: Cercano, enérgico.
        """
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=80
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Error GPT Coach: {e}")
            return None

    def _generate_chart(self, user, stats):
        try:
            # Datos
            labels = ['Mes Pasado', 'Este Mes']
            values = [stats['last_month_mtd'], stats['current_month']]
            colors = ['#94a3b8', '#4f46e5'] # Slate-400 y Indigo-600
            
            # Plot
            plt.figure(figsize=(6, 4))
            bars = plt.bar(labels, values, color=colors, width=0.6)
            plt.title(f"Gastos: {user.business_name}", fontsize=12, fontweight='bold')
            plt.ylabel('Euros (€)')
            plt.grid(axis='y', linestyle='--', alpha=0.5)
            
            # Guardar
            filename = f"chart_{user.user_phone}_{datetime.now().strftime('%Y%m%d%H%M')}.png"
            # Ruta absoluta para guardar
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # Ajustar ruta: TICKETIA_PRO es donde está este módulo. Subir 2 niveles desde 'modules/proactive'
            # base_dir debería ser la raíz de TICKETIA_PRO si __file__ es .../modules/proactive/business_health.py
            # __file__ = .../TICKETIA_PRO/modules/proactive/business_health.py
            # dirname = .../modules/proactive
            # dirname = .../modules
            # dirname = .../TICKETIA_PRO
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            save_path = os.path.join(base_dir, "static", "generated_docs", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            plt.savefig(save_path, bbox_inches='tight', dpi=100)
            plt.close()
            
            # Devolver ruta relativa web
            return f"/static/generated_docs/{filename}"
        except Exception as e:
            print(f"❌ Error Chart: {e}")
            return None

    def _send_whatsapp_with_media(self, phone, body, media_path):
        try:
            to_num = phone if phone.startswith('+') else f"+34{phone}"
            
            # Twilio necesita URL absoluta. Usamos Ngrok/Dominio si existe, o IP local.
            # Para DEMO: Asumimos que app.py corre en el dominio público configurado.
            # Intenta obtener el dominio de una variable, si no, usa una placeholder para que lo cambies.
            # IMPORTANTE: En producción usar request.host_url si es request context, pero aquí es background task.
            # Hardcodearemos el ngrok actual del usuario para que funcione YA en la demo,
            # O mejor, usar una variable de entorno.
            domain = os.environ.get("Config.PUBLIC_URL", "https://ticketia.alejbrata.ngrok.app") # Placeholder safe
            # Nota: Si el usuario tiene otro ngrok, fallará la imagen. Le avisaré para que configure .env o similar.
            
            # Recuperar dominio dinámicamente si es posible? No fácil en background task sin app_context request.
            # Usaré una variable de entorno ficticia que asumo está seteada o el usuario debe setear.
            # El prompt sugiere: domain = os.environ.get("PUBLIC_URL", "https://tudominio.ngrok-free.app")
            
            domain = os.environ.get("PUBLIC_URL", "http://localhost:5000") # Fallback local
            
            if media_path:
                # Asegurar slash
                if not media_path.startswith('/'): media_path = '/' + media_path
                media_url = f"{domain}{media_path}"
            else:
                media_url = None
            
            msg_args = {"from_": self.whatsapp_from, "to": f"whatsapp:{to_num}", "body": body}
            if media_url:
                msg_args["media_url"] = [media_url]
                
            self.twilio.messages.create(**msg_args)
            print(f"✅ Mensaje Visual enviado a {to_num} (Media: {media_url})")
        except Exception as e:
            print(f"❌ Error Twilio: {e}")
