import os
import json
from datetime import datetime
from openai import OpenAI
from core.db_models import db, Grant, ActivityLog
from modules.services.notification import NotificationService

class GrantHunterAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def check_new_grants(self, user):
        """
        Busca nuevas ayudas para un usuario específico y le notifica si encuentra algo relevante.
        """
        print(f"🔎 GrantHunter: Revisando oportunidades para {user.business_name}...")
        
        # 1. Obtener Ayudas Disponibles (que no hayan caducado)
        # Nota: En un sistema real filtraríamos por fecha > hoy. Aquí simplificamos.
        all_grants = Grant.query.all()
        
        # 2. Perfil del Usuario
        user_sector = user.static_knowledge.get('sector', 'General') if user.static_knowledge else 'General'
        user_location = user.static_knowledge.get('location', 'España') if user.static_knowledge else 'España'
        
        relevant_grants = []

        for grant in all_grants:
            # A. Filtro Anti-Spam (Ya notificado)
            # grant.notified_phones es una lista de JSON Strings o telefonos simples?
            # Asumimos lista simple de strings.
            notified_list = grant.notified_phones or []
            if user.user_phone in notified_list:
                continue

            # B. Filtro Rápido (Keyword Matching) - Ahorra Tokens
            # Si el sector de la ayuda es "General" o coincide con el del usuario, pasa.
            # Si no, usamos IA para desambiguar (ej: "Hostelería" vs "Restaurante").
            is_match = False
            
            if grant.sector_focus == "General":
                is_match = True
            elif user_sector.lower() in grant.sector_focus.lower():
                is_match = True
            else:
                # C. Matching IA (Solo si hay duda razonable)
                is_match = self._ai_match(user_sector, user_location, grant)
            
            if is_match:
                relevant_grants.append(grant)

        # 3. Notificar (Solo las Top 1 o 2 para no saturar)
        for grant in relevant_grants[:2]: 
            self._notify_grant(user, grant)
            
            # Actualizar Estado
            current_notified = list(grant.notified_phones or [])
            current_notified.append(user.user_phone)
            grant.notified_phones = current_notified
            db.session.commit()

    def _ai_match(self, user_sector, user_location, grant):
        """
        Usa GPT-4o-mini (más barato) para decidir si una ayuda es relevante.
        """
        try:
            prompt = f"""
            Actúa como consultor de ayudas.
            Usuario: Sector '{user_sector}', Ubicación '{user_location}'.
            Ayuda: '{grant.title}' para sector '{grant.sector_focus}'. Descripción: {grant.description}.
            
            ¿Es ALTA la probabilidad de que esta ayuda le interese y aplique?
            Responde SOLO 'SI' o 'NO'.
            """
            
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini", # Usamos modelo eficiente
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0
            )
            return "SI" in resp.choices[0].message.content.upper()
        except Exception as e:
            print(f"⚠️ Error AI Match: {e}")
            return False # Ante la duda, no spamear

    def _notify_grant(self, user, grant):
        """
        Genera un mensaje persuasivo y lo envía por WhatsApp.
        """
        try:
            # 1. Personalizar Mensaje con IA
            prompt = f"""
            Escribe un mensaje de WhatsApp CORTO (max 50 palabras) y EMOCIONANTE para el dueño de un negocio ({user.business_name}).
            Avísale de esta ayuda: {grant.title} ({grant.amount}).
            Dile por qué le conviene. Usa emojis.
            Al final pon: "Escribe 'QUIERO' y te la pido."
            """
            
            resp = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            pitch_text = resp.choices[0].message.content
            
            # 2. Enviar
            full_msg = f"💰 *¡Oportunidad Detectada!*\n\n{pitch_text}\n\nℹ️ Info: {grant.link}\n⏳ Límite: {grant.deadline}"
            
            # Usar Servicio Centralizado
            # 1. In-App Notification (Prioridad 1: Core de la App)
            NotificationService.send_in_app(
                user_phone=user.user_phone,
                title="💰 Nueva Ayuda Disponible",
                message=f"{pitch_text}\n\nCuantía: {grant.amount}. Plazo: {grant.deadline}.",
                type="grant",
                link=grant.link
            )
            
            # 2. WhatsApp (Opcional / Canal Secundario)
            # Solo si el usuario tiene activas las notificaciones push (futuro setting)
            try:
                account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
                auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
                client = Client(account_sid, auth_token)
                
                from_whatsapp = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
                to_whatsapp = f"whatsapp:{user.user_phone}" if "whatsapp:" not in user.user_phone else user.user_phone
                
                client.messages.create(
                    body=full_msg,
                    from_=from_whatsapp,
                    to=to_whatsapp
                )
                print(f"✅ Notificación WhatsApp enviada a {user.user_phone}")
            except Exception as twilio_err:
                print(f"⚠️ Error enviando WhatsApp (pero In-App OK): {twilio_err}")
            
            ActivityLog.log(user.user_phone, "Grant Hunter", f"Avisado de ayuda: {grant.title}")
            
        except Exception as e:
            print(f"❌ Error notificando ayuda: {e}")
