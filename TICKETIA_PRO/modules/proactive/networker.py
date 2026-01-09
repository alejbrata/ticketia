import os
import json
import random
from twilio.rest import Client
from openai import OpenAI
from core.db_models import db, BusinessProfile, SynergyMatch

class SynergyAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.twilio = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        self.whatsapp_from = "whatsapp:+14155238886"

    def run_daily_networking(self, user):
        """
        Busca UN candidato compatible para 'user' y se lo sugiere.
        """
        print(f"🤝 Networker: Buscando aliados para {user.business_name}...")
        
        # 1. Obtener candidatos (excluyendo al propio usuario)
        candidates = BusinessProfile.query.filter(BusinessProfile.id != user.id).all()
        random.shuffle(candidates)
        
        for candidate in candidates[:3]: # Analizar max 3 por ejecución
            
            # Chequear si ya se han presentado (en cualquier dirección)
            existing = SynergyMatch.query.filter(
                ((SynergyMatch.user_a_phone == user.user_phone) & (SynergyMatch.user_b_phone == candidate.user_phone)) |
                ((SynergyMatch.user_a_phone == candidate.user_phone) & (SynergyMatch.user_b_phone == user.user_phone))
            ).first()
            
            if existing:
                continue 
                
            # 2. Análisis de Sinergia con GPT-4o
            synergy = self._analyze_synergy(user, candidate)
            
            if synergy and synergy.get('score', 0) >= 75:
                # 3. ¡Es un Match! Guardar y Notificar
                self._save_match(user, candidate, synergy)
                self._notify_user(user, candidate, synergy['reason'])
                return # Solo 1 sugerencia por día

    def _analyze_synergy(self, user_a, user_b):
        info_a = f"{user_a.business_name} ({user_a.static_knowledge.get('sector', 'Varios')}). Servicios: {user_a.static_knowledge.get('services', '')}"
        info_b = f"{user_b.business_name} ({user_b.static_knowledge.get('sector', 'Varios')}). Servicios: {user_b.static_knowledge.get('services', '')}"
        
        prompt = f"""
        Analiza si estas dos empresas tienen sinergia comercial B2B.
        A: {info_a}
        B: {info_b}
        Devuelve JSON: {{ "score": (0-100), "reason": "Motivo corto" }}
        """
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=150
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"❌ Error IA Synergy: {e}")
            return None

    def _save_match(self, user, candidate, synergy):
        match = SynergyMatch(
            user_a_phone=user.user_phone,
            user_b_phone=candidate.user_phone,
            score=synergy['score'],
            reason=synergy['reason']
        )
        db.session.add(match)
        db.session.commit()

    def _notify_user(self, user, candidate, reason):
        try:
            msg = (
                f"🤝 *Networking Ticketia*\n\n"
                f"Hola {user.business_name}, posible aliado detectado:\n"
                f"🏢 *{candidate.business_name}*\n"
                f"💡 {reason}\n\n"
                f"¿Te interesa? Su contacto es: {candidate.user_phone}"
            )
            to_num = user.user_phone if user.user_phone.startswith('+') else f"+34{user.user_phone}"
            self.twilio.messages.create(from_=self.whatsapp_from, to=f"whatsapp:{to_num}", body=msg)
            print(f"✅ Sinergia enviada a {user.business_name}")
        except Exception as e:
            print(f"❌ Error WhatsApp: {e}")
