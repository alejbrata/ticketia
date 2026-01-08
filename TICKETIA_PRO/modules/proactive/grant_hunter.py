import os
from twilio.rest import Client
from openai import OpenAI
from core.db_models import db, Grant

class GrantHunterAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.twilio = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        self.whatsapp_from = "whatsapp:+14155238886" # Ajustar si es necesario

    def check_new_grants(self, user):
        print(f"🔎 GrantHunter: Revisando para {user.business_name}...")
        grants = Grant.query.all()
        user_sector = user.static_knowledge.get('sector', 'General')
        
        for grant in grants:
            # 1. Filtro Anti-Spam
            notified = grant.notified_phones or []
            if user.user_phone in notified:
                continue

            # 2. Matching IA
            if self._is_relevant(user_sector, grant):
                self._notify(user.user_phone, grant)
                # Guardar estado
                notified.append(user.user_phone)
                grant.notified_phones = list(notified)
                db.session.commit()

    def _is_relevant(self, user_sector, grant):
        if grant.sector_focus == "General": return True
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Usuario sector: {user_sector}. Ayuda para: {grant.sector_focus}. ¿Es relevante? Responde SI o NO."}],
                max_tokens=2
            )
            return "SI" in resp.choices[0].message.content.upper()
        except: return False

    def _notify(self, phone, grant):
        try:
            msg = f"💰 *Nueva Ayuda Detectada*\n\nHola, he visto esto para ti:\n📌 {grant.title}\n💵 {grant.amount}\n⏳ Fin: {grant.deadline}\n\nInfo: {grant.link}"
            self.twilio.messages.create(from_=self.whatsapp_from, to=f"whatsapp:{phone}", body=msg)
            print(f"✅ Notificado: {phone}")
        except Exception as e:
            print(f"❌ Error Twilio: {e}")
