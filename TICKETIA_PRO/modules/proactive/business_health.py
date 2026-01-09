import os
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
        
        # Si no hay datos suficientes, no decimos nada aún
        if stats['current_month'] == 0 and stats['last_month'] == 0:
            return

        # 2. Generar Mensaje con IA (Personalidad Coach)
        message = self._generate_coach_message(user.business_name, stats)
        
        # 3. Enviar WhatsApp
        if message:
            self._send_whatsapp(user.user_phone, message)

    def _get_financial_stats(self, phone):
        today = datetime.now()
        start_current = today.replace(day=1, hour=0, minute=0, second=0)
        
        # Mes pasado completo (para referencia) o MTD (Month to Date)?
        # Mejor MTD: Comparar los primeros X días de este mes vs primeros X días del mes pasado.
        start_last = (start_current - relativedelta(months=1))
        end_last_comparable = start_last + timedelta(days=today.day) # Mismo día del mes pasado
        
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

        Escribe un mensaje de WhatsApp CORTO (máx 2 frases + emojis).
        - Si ha gastado MENOS (variación negativa): Felicítalo, usa emojis de trofeos/músculo.
        - Si ha gastado MÁS (variación positiva): Dale una alerta amable pero firme, emojis de ojo/alerta.
        - Si es igual: Anímalo a seguir controlando.
        
        No uses "Hola", ve directo al grano. Tono: Cercano, enérgico y profesional.
        """
        
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=60
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Error GPT Coach: {e}")
            return None

    def _send_whatsapp(self, phone, body):
        try:
            to_num = phone if phone.startswith('+') else f"+34{phone}"
            self.twilio.messages.create(
                from_=self.whatsapp_from,
                to=f"whatsapp:{to_num}",
                body=f"🩺 *Reporte Financiero Di*\n\n{body}"
            )
            print(f"✅ Coach message sent to {phone}")
        except Exception as e:
            print(f"❌ Error Twilio: {e}")
