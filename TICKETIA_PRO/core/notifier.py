import os
from twilio.rest import Client
from core.config import Config
from core.db_models import ActivityLog

class NotifierService:
    def __init__(self):
        # Configuración Twilio (Solo se usa si el canal es whatsapp)
        self.twilio_client = None
        sid = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        if sid and token:
            self.twilio_client = Client(sid, token)
        self.whatsapp_from = "whatsapp:+14155238886"

    def send(self, user_contact, message, media_url=None, channel='whatsapp'):
        """
        Envía un mensaje por el canal especificado.
        channel: 'whatsapp' | 'web'
        """
        print(f"📡 Notifier: Enviando a {user_contact} vía [{channel}]...")

        if channel == 'whatsapp':
            return self._send_whatsapp(user_contact, message, media_url)
        elif channel == 'web':
            return self._send_web_notification(user_contact, message, media_url)
        else:
            print(f"❌ Canal desconocido: {channel}")
            return False

    def _send_whatsapp(self, phone, body, media_url):
        if not self.twilio_client:
            print("⚠️ Twilio no configurado.")
            return False
            
        try:
            to_num = phone if "whatsapp:" in phone else f"whatsapp:{phone}"
            if not to_num.startswith("whatsapp:+"): to_num = f"whatsapp:+34{phone}" # Fallback simple

            msg_args = {
                "from_": self.whatsapp_from,
                "to": to_num,
                "body": body
            }
            if media_url:
                msg_args["media_url"] = [media_url]

            self.twilio_client.messages.create(**msg_args)
            return True
        except Exception as e:
            print(f"❌ Error Twilio: {e}")
            return False

    def _send_web_notification(self, user_id, body, media_url):
        # En una arquitectura real, esto enviaría un WebSocket o guardaría en una tabla 'Notifications'
        # Para este MVP, lo guardamos en un log que el frontend podría consultar (polling)
        
        log_msg = f"WEB MSG: {body}"
        if media_url:
            log_msg += f" | MEDIA: {media_url}"
            
        ActivityLog.log(user_id, "System Notification", log_msg)
        return True
