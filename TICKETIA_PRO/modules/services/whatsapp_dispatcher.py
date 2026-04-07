import os
from twilio.twiml.messaging_response import MessagingResponse
from core.db_models import BusinessProfile
from modules.agents.manager import run_agent

class WhatsAppWebhookDispatcher:
    """
    Dispatcher pattern for handling Twilio WhatsApp Webhooks.
    Isolates parsing, routing, and response generation into readable methods.
    """
    def __init__(self, request_values):
        self.incoming_msg = request_values.get('Body', '').strip()
        self.sender = request_values.get('From', '').replace('whatsapp:', '')
        self.target_number = request_values.get('To', '').replace('whatsapp:', '')
        self.num_media = int(request_values.get('NumMedia', 0))
        self.media_url = request_values.get('MediaUrl0') if self.num_media > 0 else None
        self.media_type = request_values.get('MediaContentType0', '') if self.num_media > 0 else ""
        self.resp = MessagingResponse()

    def process(self):
        try:
            print(f"📩 WhatsApp In: {self.sender} -> {self.target_number} | Msg: {self.incoming_msg} | Media: {self.num_media}")
            
            target_business = BusinessProfile.query.filter_by(whatsapp_number=self.target_number).first()
            
            if target_business:
                return self._handle_dedicated_client_number(target_business)
            else:
                return self._handle_ticketia_central_number()
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR webhook logic: {e}")
            self.resp.message("⚠️ Error interno del servidor.")
            return str(self.resp)

    def _handle_dedicated_client_number(self, target_business):
        """CASO 2: Escriben a un NÚMERO DEDICADO DE CLIENTE"""
        try:
            agent_response = run_agent(self.incoming_msg, self.sender, target_business)
            self.resp.message(agent_response)
        except Exception as e:
            print(f"Error invocado agente dedicado: {e}")
            self.resp.message("⚠️ El agente está experimentando problemas técnicos.")
        return str(self.resp)

    def _handle_ticketia_central_number(self):
        """CASO 1: Escriben a TICKETIA CENTRAL (o número desconocido)"""
        user_profile = BusinessProfile.query.filter_by(user_phone=self.sender).first()
        
        if not user_profile:
            print("   -> Usuario NO reconocido.")
            self.resp.message("🤖 Bienvenido a Zeptai. Para usar este bot de gastos, por favor regístrate en nuestra web.")
            return str(self.resp)
            
        print(f"   -> Usuario reconocido: {user_profile.business_name}")
        
        if self.num_media > 0:
            msg_text = self.incoming_msg.lower()
            
            if 'audio' in self.media_type:
                return self._process_audio_message(user_profile)
            else:
                return self._process_image_message(user_profile, msg_text)
        else:
            # Texto normal (Chat con el Asistente)
            agent_reply = run_agent(self.incoming_msg, self.sender, user_profile)
            self.resp.message(agent_reply)
            return str(self.resp)

    def _process_audio_message(self, user_profile):
        from modules.utils.transcriber import AudioTranscriber
        print("🎤 Detectado Audio -> Transcribiendo...")
        transcribed_text = AudioTranscriber().transcribe(self.media_url)
        
        if transcribed_text:
            try:
                agent_resp = run_agent(transcribed_text, self.sender, user_profile)
                self.resp.message(f"🎤 (Entendido: \"{transcribed_text}\")\n\n{agent_resp}")
            except Exception as e:
                print(f"Error Agent execution from audio: {e}")
                self.resp.message("⚠️ Entendí el audio pero fallé procesando la orden.")
        else:
            self.resp.message("⚠️ No he podido escuchar el audio.")
            
        return str(self.resp)

    def _process_image_message(self, user_profile, msg_text):
        from modules.tickets.logic import process_ticket
        
        features = user_profile.features or {}
        active_agents = user_profile.active_agents or []
        
        if "admin_redactor" in active_agents:
            # CEREBRO HÍBRIDO: IA decide si es Gasto o Borrador
            print(f"   -> Consultando Redactor para clasificar...")
            from modules.proactive.admin_redactor import AdminAssistantAgent
            intent = AdminAssistantAgent().classify_image_intent(self.media_url, msg_text)
            
            if intent == 'draft':
                print(f"   -> Intent: BORRADOR (Redactor)")
                agent_resp = run_agent(self.incoming_msg, self.sender, user_profile, self.media_url) # Removed mail_service=mail to decouple globals
                self.resp.message(agent_resp)
            else:
                print(f"   -> Intent: TICKET (Accounting)")
                if features.get('can_upload_tickets', True):
                    logic_response = process_ticket(self.media_url, self.sender)
                    self.resp.message(logic_response)
                else:
                    self.resp.message("⛔ Tu plan no permite subir tickets, y esto parece un ticket.")
                    
        elif features.get('can_upload_tickets', True):
            # CEREBRO TICKETIA (GASTOS)
            print(f"   -> Procesando como Gasto (Ticketia).")
            logic_response = process_ticket(self.media_url, self.sender)
            self.resp.message(logic_response)
        else:
            self.resp.message("⛔ Tu plan actual no incluye gestión de tickets.")
            
        return str(self.resp)
