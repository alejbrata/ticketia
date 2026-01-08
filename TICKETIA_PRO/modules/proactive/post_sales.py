import os
from datetime import datetime, timedelta
from twilio.rest import Client
from core.db_models import db, Appointment, BusinessProfile

class PostSalesAgent:
    def __init__(self):
        self.twilio = Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        self.whatsapp_from = "whatsapp:+14155238886"

    def run_daily_checks(self, business_profile):
        """Ejecuta todas las estrategias post-venta para el negocio."""
        print(f"🔄 Post-Sales: Ejecutando ciclo para {business_profile.business_name}...")
        
        # Leer Configuración (Defaults: Feedback OFF, Reactivation ON)
        user_config = getattr(business_profile, 'agent_config', {}) or {}
        config = user_config.get('post_sales_service', {})
        enable_feedback = config.get('enable_feedback', False)
        enable_reactivation = config.get('enable_reactivation', True)
        
        # 1. Estrategia de Calidad (Feedback 24h)
        if enable_feedback:
            self._run_feedback_loop(business_profile)
        else:
            print("   -> Feedback loop desactivado por configuración.")
        
        # 2. Estrategia de Retención (Rescate 90 días)
        if enable_reactivation:
            offer_type = config.get('offer_type', '10% de Descuento')
            custom_text = config.get('custom_offer_text', '')
            self._run_reactivation_loop(business_profile, offer_type, custom_text)
        else:
            print("   -> Reactivation loop desactivado por configuración.")

    def _run_feedback_loop(self, business):
        """Clientes de AYER -> Pedir Reseña"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        # Buscamos citas de ayer
        appts = Appointment.query.filter_by(business_phone=business.user_phone, date=yesterday).all()
        
        for appt in appts:
            if appt.client_phone:
                msg = (
                    f"👋 Hola {appt.client_name}, gracias por venir ayer a *{business.business_name}*.\n"
                    f"¿Qué tal fue todo? ⭐ Nos ayuda mucho tu valoración."
                )
                self._send_whatsapp(appt.client_phone, msg)

    def _run_reactivation_loop(self, business, offer_type="10% de Descuento", custom_text=""):
        """Clientes de hace 3 MESES que no han vuelto -> Oferta"""
        target_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # 1. Buscar citas de hace exactamente 90 días
        old_appts = Appointment.query.filter_by(business_phone=business.user_phone, date=target_date).all()
        
        for old_appt in old_appts:
            # 2. Verificar si han vuelto desde entonces
            has_returned = Appointment.query.filter(
                Appointment.business_phone == business.user_phone,
                Appointment.client_phone == old_appt.client_phone,
                Appointment.date > target_date
            ).first()
            
            if not has_returned and old_appt.client_phone:
                # 3. Construir mensaje según oferta
                offer_msg = ""
                if offer_type == "10% de Descuento":
                    offer_msg = "tienes un **10% de DESCUENTO** si vienes esta semana. 🏷️"
                elif offer_type == "Regalo Especial":
                    offer_msg = "te invitamos a un **POSTRE o REGALO** en tu próxima visita. 🎁"
                elif offer_type == "2x1":
                    offer_msg = "tienes un **2x1** esperándote. ✌️"
                elif offer_type == "Custom" and custom_text:
                    offer_msg = f"{custom_text} ✨"
                else:
                    offer_msg = "tienes un detalle especial de nuestra parte. 🎁"
                
                msg = (
                    f"📅 Hola {old_appt.client_name}, ¡hace mucho que no te vemos en *{business.business_name}*!\n\n"
                    f"Te echamos de menos. Por eso, {offer_msg}\n"
                    f"¿Te agendo cita?"
                )
                self._send_whatsapp(old_appt.client_phone, msg)
                print(f"   🎣 Intento de rescate ({offer_type}) enviado a {old_appt.client_name}")

    def _send_whatsapp(self, phone, body):
        try:
            to_num = phone if phone.startswith('+') else f"+34{phone}"
            self.twilio.messages.create(
                from_=self.whatsapp_from,
                to=f"whatsapp:{to_num}",
                body=body
            )
        except Exception as e:
            print(f"   ❌ Error WhatsApp: {e}")
