import os
import json
import logging
import time
from datetime import datetime
from threading import Thread

from core.clients import get_openai_client
from core.llm_tracker import track as _track

logger = logging.getLogger(__name__)
from core.db_models import Ticket, ActivityLog, GeneratedDocument, db
from modules.agents.tools import CalendarTools, TOOLS_SCHEMA
from modules.agents.history import HistoryService
from modules.agents.background_tasks import run_marketing_thread

class AgentExecutor:
    """
    Handles the execution cycle of the AI agent, including tool usage, memory, and routing.
    Always operates in web/PWA channel — WhatsApp removed.
    """
    def __init__(self, user_message, phone_number, business_profile, media_url=None, mail_service=None):
        self.user_message = user_message
        self.phone_number = phone_number
        self.business_profile = business_profile
        self.media_url = media_url
        self.mail_service = mail_service
        self.client = get_openai_client()
        self.host_url = os.environ.get('PUBLIC_URL', 'http://localhost:5000').rstrip('/') + '/'

    @property
    def system_prompt(self):
        sp = self.business_profile.system_prompt
        if not sp:
            sp = f"Eres un asistente IA inteligente para la empresa {self.business_profile.business_name}. Ayuda al usuario con sus tareas de gestión, presupuestos y dudas."
        return sp

    def execute(self):
        try:
            # 1. DISPATCHER DE IMÁGENES (ADMIN REDACTOR)
            if self.media_url and "admin_redactor" in (self.business_profile.active_agents or []):
                return self._handle_image_direct_processing()

            # 2. Guardar Mensaje del Usuario
            HistoryService.save_interaction(self.phone_number, "user", self.user_message)

            # 3. Construir Contexto
            history = HistoryService.get_recent_history(self.phone_number, limit=10)
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(history)

            # 4. LLM Generation
            _t0 = time.time()
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
            _track(self.phone_number, "gpt-4o", "chat_main",
                   response, int((time.time() - _t0) * 1000))

            response_message = response.choices[0].message
            final_content = response_message.content

            # 5. Execute Tools Sequence
            if response_message.tool_calls:
                messages.append(response_message)
                final_content = self._process_tool_calls(messages, response_message.tool_calls)

            # 6. Guardar Respuesta Final
            if final_content:
                HistoryService.save_interaction(self.phone_number, "assistant", final_content)

            return final_content

        except Exception as e:
            logger.error("Error AgentExecutor [%s]: %s", self.phone_number, e)
            return "⚠️ Lo siento, tuve un problema interno procesando tu solicitud."

    def _handle_image_direct_processing(self):
        from modules.proactive.admin_redactor import AdminAssistantAgent
        pdf_path = AdminAssistantAgent().process_image_request(self.media_url, {
            "business_name": self.business_profile.business_name,
            "phone": self.business_profile.user_phone,
            "email": self.business_profile.email,
            "extra_info": self.business_profile.static_knowledge or {}
        })

        if pdf_path:
            full_url = f"{self.host_url.rstrip('/')}{pdf_path}"
            msg_text = f"✅ ¡Hecho! Aquí tienes tu documento formalizado:\n{full_url}"
            ActivityLog.log(self.phone_number, "Admin Redactor", "Procesada imagen (Multimodal)")

            if self.mail_service and self.business_profile.email:
                try:
                    from flask_mail import Message
                    with open(pdf_path.lstrip('/'), 'rb') as fp:
                        msg = Message(
                            subject=f"Nuevo Documento Generado: {os.path.basename(pdf_path)}",
                            sender=os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@ticketia.com'),
                            recipients=[self.business_profile.email],
                            body=f"Hola {self.business_profile.business_name},\n\nAquí tienes el documento generado desde tu última captura.\n\nSaludos,\nTu Agente IA."
                        )
                        msg.attach(os.path.basename(pdf_path), "application/pdf", fp.read())
                        self.mail_service.send(msg)
                        msg_text += "\n\n📧 También te lo he enviado a tu correo."
                except Exception as e:
                    logger.error("Error enviando email: %s", e)
            return msg_text
        return "❌ No pude procesar la imagen. Asegúrate de que se ve bien el texto."

    def _process_tool_calls(self, messages, tool_calls):
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_output = None

            if function_name == "check_availability":
                tool_output = CalendarTools.check_availability(
                    date=function_args.get("date"),
                    business_phone=self.business_profile.user_phone
                )
                ActivityLog.log(self.phone_number, "Calendar Agent", f"Consultada agenda: {function_args.get('date')}")

            elif function_name == "book_appointment":
                tool_output = CalendarTools.book_appointment(
                    date=function_args.get("date"),
                    time=function_args.get("time"),
                    client_name=function_args.get("client_name"),
                    phone=function_args.get("phone"),
                    business_phone=self.business_profile.user_phone
                )
                ActivityLog.log(self.phone_number, "Calendar Agent", f"Cita agendada: {function_args.get('client_name')}")

            elif function_name == "create_proposal_from_last_image":
                tool_output = self._tool_create_proposal_from_last_image()

            elif function_name == "create_proposal_from_text":
                tool_output = self._tool_create_proposal_from_text(function_args)

            elif function_name == "generate_marketing_material":
                tool_output = self._tool_generate_marketing(function_args)
                if tool_output.startswith("⏳"):
                    HistoryService.save_interaction(self.phone_number, "assistant", tool_output)
                    return tool_output

            elif function_name == "handle_customer_service":
                from modules.proactive.post_sales import PostSalesAgent
                last_user_msg = "Consulta general"
                for m in reversed(messages):
                    role = m.get('role') if isinstance(m, dict) else getattr(m, 'role', None)
                    content = m.get('content') if isinstance(m, dict) else getattr(m, 'content', None)
                    if role == 'user':
                        last_user_msg = content
                        break

                agent = PostSalesAgent()
                resp_text, media_url = agent.handle_inquiry(self.phone_number, last_user_msg, self.business_profile)
                tool_output = resp_text

            else:
                tool_output = "Error: Herramienta desconocida."

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_output
            })

        # Segunda llamada a OpenAI (tras tool execution)
        _t0 = time.time()
        final_response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        _track(self.phone_number, "gpt-4o", "chat_tool_followup",
               final_response, int((time.time() - _t0) * 1000))
        return final_response.choices[0].message.content

    def _tool_create_proposal_from_last_image(self):
        last_ticket = Ticket.query.filter_by(user_phone=self.phone_number).order_by(Ticket.date.desc()).first()
        if last_ticket and last_ticket.image_path:
            from modules.proactive.admin_redactor import AdminAssistantAgent
            assistant = AdminAssistantAgent()

            sk = self.business_profile.static_knowledge or {}
            if isinstance(sk, str):
                try: sk = json.loads(sk)
                except json.JSONDecodeError: sk = {}

            pdf_path = assistant.process_image_request(last_ticket.image_path, {
                "business_name": self.business_profile.business_name,
                "phone": self.business_profile.user_phone,
                "email": self.business_profile.email,
                "sector": sk.get('sector', 'Servicios'),
                "extra_info": sk
            })

            if pdf_path:
                try:
                    new_doc = GeneratedDocument(
                        user_phone=self.phone_number,
                        file_path=pdf_path,
                        doc_type='proposal',
                        client_name="Presupuesto (Imagen)",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_doc)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error("Error guardando documento en DB: %s", e)

                ActivityLog.log(self.phone_number, "Admin Redactor", "Generado presupuesto desde Imagen")
                return f"✅ Documento generado de la última imagen: {self.host_url.rstrip('/')}{pdf_path}"
            return "❌ Hubo un error procesando la imagen."
        return "❌ No encuentro ninguna imagen reciente subida como ticket."

    def _tool_create_proposal_from_text(self, function_args):
        from modules.proactive.admin_redactor import AdminAssistantAgent
        data_payload = {
            "client_name": function_args.get("client_name"),
            "items": function_args.get("items"),
            "total": function_args.get("total"),
            "notes": function_args.get("notes"),
            "date": datetime.now().strftime('%d/%m/%Y')
        }

        assistant = AdminAssistantAgent()
        sk = self.business_profile.static_knowledge or {}
        if isinstance(sk, str):
            try: sk = json.loads(sk)
            except: sk = {}

        pdf_path = assistant.generate_proposal_from_data(data_payload, {
            "business_name": self.business_profile.business_name,
            "phone": self.business_profile.user_phone,
            "email": self.business_profile.email,
            "sector": sk.get('sector', 'Servicios'),
            "extra_info": sk
        })

        if pdf_path:
            try:
                new_doc = GeneratedDocument(
                    user_phone=self.phone_number,
                    file_path=pdf_path,
                    doc_type='proposal',
                    client_name=function_args.get("client_name") or "Cliente General",
                    created_at=datetime.utcnow()
                )
                db.session.add(new_doc)
                db.session.commit()
                ActivityLog.log(self.phone_number, "Admin Redactor", f"Generado presupuesto: {function_args.get('client_name')}")
                return "Se ha generado el documento correctamente. Puedes verlo en la sección Documentos."
            except Exception as e:
                db.session.rollback()
                logger.error("Error guardando propuesta en DB: %s", e)
                return "El PDF se generó físicamente, pero hubo un error guardándolo en tu historial."
        return "❌ Hubo un error generando el PDF físico."

    def _tool_generate_marketing(self, function_args):
        prompt_text = function_args.get("prompt")
        fmt = function_args.get("format")
        empresa = self.business_profile.business_name
        logo_path_db = self.business_profile.logo_path

        run_marketing_thread(
            user_phone=self.phone_number,
            prompt=prompt_text,
            format_type=fmt,
            host_url=self.host_url,
            p_business_name=empresa,
            p_logo_path=logo_path_db,
        )
        ActivityLog.log(self.phone_number, "Marketing Agent", f"Iniciado diseño: {prompt_text[:30]}...")
        return "⏳ ¡Oído! Me pongo a diseñarlo ahora mismo. Tardaré unos 20-30 segundos. Te avisaré cuando esté listo. 🚀"


def run_agent(user_message, phone_number, business_profile, media_url=None, mail_service=None, channel=None):
    """
    Wrapper para mantener compatibilidad con el resto de la aplicación.
    El parámetro channel se ignora — la app opera exclusivamente en modo web/PWA.
    """
    executor = AgentExecutor(user_message, phone_number, business_profile, media_url, mail_service)
    return executor.execute()
