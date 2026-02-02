import os
import matplotlib
matplotlib.use('Agg') # Backend sin interfaz gráfica
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from openai import OpenAI
from core.db_models import db, Ticket
from core.notifier import NotifierService

from core.config import Config

class BusinessCoachAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.notifier = NotifierService()
        # Eliminar self.twilio y self.whatsapp_from (ahora gestionado por NotifierService)

    def run_daily_analysis(self, user):
        """
        Analiza la salud financiera y envía feedback MULTIMODAL (Texto + Gráfico + Audio).
        """
        print(f"🩺 Coach: Analizando finanzas de {user.business_name}...")
        
        # 1. Obtener Datos
        stats = self._get_financial_stats(user.user_phone)
        
        # Check simple para no hablar si no hay datos (ajustar según necesidad demo)
        if stats['current_month'] == 0 and stats['last_month_mtd'] == 0:
            print("   -> Sin datos suficientes.")
            return

        # 2. Generar Contenido
        message_text = self._generate_coach_message(user.business_name, stats)
        
        # Generar Gráfico (Visual)
        chart_url = self._generate_chart(user, stats)
        
        # Generar Audio (Voz) - NUEVO
        audio_url = self._generate_audio(message_text)
        
        # 3. Enviar Multimodal (Texto + Array de Media)
        if message_text:
            media_list = []
            if chart_url: media_list.append(chart_url)
            if audio_url: media_list.append(audio_url)
            
            self._send_whatsapp_multimodal(user.user_phone, message_text, media_list)

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
            
            save_path = os.path.join(base_dir, "static", "generated_docs", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            plt.savefig(save_path, bbox_inches='tight', dpi=100)
            plt.close()
            
            # Devolver ruta relativa web
            return f"{Config.PUBLIC_URL}/static/generated_docs/{filename}"
        except Exception as e:
            print(f"❌ Error Chart: {e}")
            return None

    def _generate_audio(self, text):
        """Genera un archivo de audio MP3 usando OpenAI TTS."""
        try:
            print("   🎙️ Generando voz del coach...")
            response = self.openai.audio.speech.create(
                model="tts-1",
                voice="onyx", # Voces disponibles: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )
            
            filename = f"voice_{int(datetime.now().timestamp())}.mp3"
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            save_path = os.path.join(base_dir, "static", "generated_docs", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Guardar archivo
            response.stream_to_file(save_path)
            
            # Devolver URL Absoluta
            return f"{Config.PUBLIC_URL}/static/generated_docs/{filename}"
            
        except Exception as e:
            print(f"❌ Error TTS: {e}")
            return None

    def _send_whatsapp_multimodal(self, phone, body, media_urls=[]):
        """Envía mensaje con lista de adjuntos usando el NotifierService."""
        # Enviar Texto primero
        self.notifier.send(phone, body, channel='whatsapp') # Por defecto Coach usa whatsapp
        
        # Enviar Medios
        # Nota: El NotifierService simple envía 1 adjunto por mensaje.
        # Si queremos enviar todos juntos, tendríamos que mejorar el NotifierService o iterar.
        # Iteramos por simplicidad y compatibilidad con el código anterior.
        for media in media_urls:
            if media:
                self.notifier.send(phone, "Adjunto:", media_url=media, channel='whatsapp')


