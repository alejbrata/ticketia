import os
import json
import random
from twilio.rest import Client
from openai import OpenAI
from core.db_models import db, BusinessProfile, SynergyMatch, Ticket, ActivityLog
from modules.services.notification import NotificationService

class SynergyAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def run_daily_networking(self, user):
        """
        Busca aliados estratégicos basándose en perfil y COMPORTAMIENTO DE COMPRA (Tickets).
        """
        print(f"🤝 Networker: Buscando aliados para {user.business_name}...")
        
        # 1. Enriquecer Perfil con Historial de Compras (Mining)
        user_spending_profile = self._get_spending_profile(user)
        
        # 2. Obtener candidatos (excluyendo al propio usuario)
        candidates = BusinessProfile.query.filter(BusinessProfile.id != user.id).all()
        # Priorizar candidatos con sectores complementarios (simple heuristic first)
        random.shuffle(candidates)
        
        match_found = False
        
        for candidate in candidates[:5]: # Analizar max 5 por ejecución
            
            # Evitar repetidos
            existing = SynergyMatch.query.filter(
                ((SynergyMatch.user_a_phone == user.user_phone) & (SynergyMatch.user_b_phone == candidate.user_phone)) |
                ((SynergyMatch.user_a_phone == candidate.user_phone) & (SynergyMatch.user_b_phone == user.user_phone))
            ).first()
            
            if existing: continue 
                
            # 3. Análisis de Sinergia Profundo con GPT-4o
            synergy = self._analyze_synergy_deep(user, user_spending_profile, candidate)
            
            if synergy and synergy.get('score', 0) >= 80: # Subimos el listón a 80
                # 4. ¡Es un Match! Guardar y Notificar
                self._save_match(user, candidate, synergy)
                self._notify_intro(user, candidate, synergy['reason'])
                match_found = True
                break # Solo 1 sugerencia por día para no saturar

        if not match_found:
            print(f"🤷‍♂️ Networker: No encontré matches hoy para {user.business_name}")

    def _get_spending_profile(self, user):
        """
        Analiza los últimos 10 tickets para entender en qué gasta la empresa.
        """
        tickets = Ticket.query.filter_by(user_phone=user.user_phone).order_by(Ticket.date.desc()).limit(10).all()
        if not tickets: return "Sin historial de compras reciente."
        
        concepts = [t.concept or "Gasto vario" for t in tickets]
        providers = [t.provider or "Desconocido" for t in tickets]
        
        summary = f"Últimos gastos en: {', '.join(concepts[:5])}. Proveedores frecuentes: {', '.join(providers[:3])}."
        return summary

    def _analyze_synergy_deep(self, user_a, spending_a, user_b):
        """
        Analiza sinergia usando perfil declarado + perfil de gasto.
        """
        info_a = f"Empresa A: {user_a.business_name} ({user_a.static_knowledge.get('sector', 'Varios')}).\nPerfil de Gasto A: {spending_a}"
        info_b = f"Empresa B: {user_b.business_name} ({user_b.static_knowledge.get('sector', 'Varios')}).\nServicios B: {user_b.static_knowledge.get('services', 'General')}"
        
        prompt = f"""
        Actúa como consultor de negocios B2B experto.
        Analiza si hay una oportunidad de negocio CLARA entre A y B.
        
        {info_a}
        
        {info_b}
        
        Busca:
        1. Relación Cliente-Proveedor (A gasta en lo que B vende).
        2. Alianza Estratégica (Ej: Gimnasio + Tienda Suplementos).
        
        Devuelve JSON: {{ "score": (0-100), "reason": "Frase corta y persuasiva para A explicando por qué conectar con B." }}
        """
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=150,
                temperature=0.3
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"❌ Error IA Synergy: {e}")
            return None

    def _save_match(self, user_a, user_b, synergy):
        match = SynergyMatch(
            user_a_phone=user_a.user_phone,
            user_b_phone=user_b.user_phone,
            score=synergy['score'],
            reason=synergy['reason'],
            status='pending' # Nuevo estado
        )
        db.session.add(match)
        db.session.commit()
        ActivityLog.log(user_a.user_phone, "Networker Agent", f"Match sugerido: {user_b.business_name}")

    def _notify_intro(self, user, candidate, reason):
        """
        Envía la sugerencia al usuario A (App + WhatsApp opcional).
        """
        try:
            # 1. Notificación In-App (Core)
            NotificationService.send_in_app(
                user_phone=user.user_phone,
                title="🤝 Nueva Oportunidad de Negocio",
                message=f"Creemos que deberías colaborar con {candidate.business_name}.\n\n💡 Motivo: {reason}\n\n¿Te interesa conectar?",
                type="networking",
                link="/networking" # Futuro dashboard de networking
            )
            
            # 2. WhatsApp (Canal Secundario / Push)
            msg = (
                f"🤝 *Networking Ticketia*\n\n"
                f"Hola {user.business_name}, tienes una nueva oportunidad de negocio esperándote en la app.\n"
                f"Entra para ver los detalles: https://ticketia.com/dashboard"
            )
            
            # Lógica Twilio con fallback
            try:
                account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
                auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
                client = Client(account_sid, auth_token)
                
                from_whatsapp = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
                to_whatsapp = f"whatsapp:{user.user_phone}" if "whatsapp:" not in user.user_phone else user.user_phone
                
                client.messages.create(
                    body=msg,
                    from_=from_whatsapp,
                    to=to_whatsapp
                )
                print(f"✅ Aviso WhatsApp enviado a {user.business_name}")
            except Exception as twilio_e:
                 print(f"⚠️ Error WhatsApp (pero In-App OK): {twilio_e}")
            
            ActivityLog.log(user.user_phone, "Networker Agent", f"Sinergia sugerida: {candidate.business_name}")
            
        except Exception as e:
            print(f"❌ Error General Notification: {e}")
