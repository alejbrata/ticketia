import os
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from openai import OpenAI
from core.db_models import db, Ticket, ActivityLog
from modules.services.notification import NotificationService

class BusinessCoachAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def run_daily_analysis(self, user):
        """
        Analiza la salud financiera y genera un informe diario (In-App + Push).
        """
        print(f"🩺 Coach: Analizando finanzas de {user.business_name}...")
        
        # 1. Obtener Datos Financieros
        stats = self._get_financial_stats(user.user_phone)
        
        # Si no hay datos, no decimos nada (salvo que sea demo)
        if stats['current_month'] == 0 and stats['last_month_total'] == 0:
            return

        # 2. Generar Insight con IA
        insight = self._generate_insight(user, stats)
        
        # 3. Notificación In-App (Rica)
        # Creamos un mensaje que invite a ver el detalle
        trend_emoji = "📈" if stats['diff_percent'] > 0 else "📉"
        if stats['diff_percent'] == 0: trend_emoji = "➡️"
        
        title = f"Resumen Diario: {trend_emoji} {stats['diff_percent']}% vs mes pasado"
        
        # Guardamos notificación
        NotificationService.send_in_app(
            user_phone=user.user_phone,
            title=title,
            message=f"{insight}\n\nGasto hoy: {stats['current_month']}€ (Proyección: {stats['projection']}€)",
            type="alert" if stats['is_alert'] else "info",
            link="/dashboard" # Lleva al dashboard para ver gráficos interactivos
        )
        
        # 4. Push Notification (WhatsApp - Solo Texto Corto)
        # Solo enviamos push si es relevante (alertas o lunes/viernes)
        # Aquí simplificamos enviando siempre un resumen corto
        try:
            push_msg = f"📊 *Coach Financiero*\n\n{insight}\n\nEntra en la app para ver el desglose completo."
            
            # Usar lógica de Twilio directa (o servicio centralizado si estuviera completo)
            from twilio.rest import Client
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
            client = Client(account_sid, auth_token)
            
            from_whatsapp = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
            to_whatsapp = f"whatsapp:{user.user_phone}" if "whatsapp:" not in user.user_phone else user.user_phone
            
            client.messages.create(body=push_msg, from_=from_whatsapp, to=to_whatsapp)
            
        except Exception as e:
            print(f"⚠️ Error Push WhatsApp: {e}")

        ActivityLog.log(user.user_phone, "Business Coach", "Informe diario generado")

    def _get_financial_stats(self, phone):
        today = datetime.now()
        start_current = today.replace(day=1, hour=0, minute=0, second=0)
        
        # Mes anterior completo
        first_day_last_month = (start_current - timedelta(days=1)).replace(day=1)
        
        # Gasto Mes Actual (MTD)
        current_total = db.session.query(func.sum(Ticket.total)).filter(
            Ticket.user_phone == phone,
            Ticket.date >= start_current
        ).scalar() or 0.0

        # Gasto Mes Pasado Total
        last_month_total = db.session.query(func.sum(Ticket.total)).filter(
            Ticket.user_phone == phone,
            Ticket.date >= first_day_last_month,
            Ticket.date < start_current
        ).scalar() or 0.0
        
        # Proyección (Regla de tres simple basada en días transcurridos)
        days_passed = today.day
        days_in_month = (start_current.replace(month=start_current.month % 12 + 1) - timedelta(days=1)).day
        
        projection = 0
        if days_passed > 0:
            projection = (current_total / days_passed) * days_in_month
            
        # Comparativa vs Mes Pasado Total
        diff_percent = 0
        if last_month_total > 0:
            # Comparamos proyección vs real mes pasado para ser justos
            diff_percent = ((projection - last_month_total) / last_month_total) * 100
            
        return {
            "current_month": round(current_total, 2),
            "last_month_total": round(last_month_total, 2),
            "projection": round(projection, 2),
            "diff_percent": round(diff_percent, 1),
            "is_alert": diff_percent > 20 # Alerta si gastamos un 20% más de lo previsto
        }

    def _generate_insight(self, user, stats):
        """
        Genera un consejo de texto corto.
        """
        prompt = f"""
        Eres el Director Financiero de {user.business_name}.
        Datos:
        - Gasto acumulado: {stats['current_month']}€
        - Proyección fin de mes: {stats['projection']}€
        - Mes pasado total: {stats['last_month_total']}€
        - Variación Proyectada: {stats['diff_percent']}%
        
        Dame 1 frase (max 20 palabras) analizando la situación.
        Si la variación es > 20%, sé alarmista. Si es < 0%, felicita por el ahorro.
        Usa emojis.
        """
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except:
            return "📊 Tus gastos siguen su curso normal. ¡Sigue así!"


