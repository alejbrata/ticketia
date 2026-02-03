import threading
from datetime import datetime
from twilio.rest import Client
import os
import json
from flask import request
from openai import OpenAI
from core.db_models import Ticket, ActivityLog
from modules.agents.tools import CalendarTools, TOOLS_SCHEMA
from modules.agents.history import HistoryService

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(user_message, phone_number, business_profile, media_url=None, mail_service=None, channel='whatsapp'):
    """
    Ejecuta el ciclo del agente con capacidad de usar herramientas, memoria y visión.
    """
    try:
        system_prompt = business_profile.system_prompt
        if not system_prompt:
            # Fallback por defecto para usuarios nuevos
            system_prompt = f"Eres un asistente IA inteligente para la empresa {business_profile.business_name}. Ayuda al usuario con sus tareas de gestión, presupuestos y dudas."

        # --- DISPATCHER DE IMÁGENES (ADMIN REDACTOR) ---
        if media_url and "admin_redactor" in (business_profile.active_agents or []):
            from modules.proactive.admin_redactor import AdminAssistantAgent
            pdf_path = AdminAssistantAgent().process_image_request(media_url, {
                "business_name": business_profile.business_name,
                "phone": business_profile.user_phone,
                "email": business_profile.email,
                "extra_info": business_profile.static_knowledge or {}
            })
            if pdf_path:
                msg_text = f"✅ ¡Hecho! Aquí tienes tu documento formalizado:\n{request.host_url.rstrip('/')}{pdf_path}"
                ActivityLog.log(phone_number, "Admin Redactor", "Procesada imagen (Multimodal)")
                
                # Enviar por correo si está disponible el servicio
                if mail_service and business_profile.email:
                    try:
                        from flask_mail import Message
                        
                        # Construir ruta al archivo
                        file_path = pdf_path.lstrip('/') # Remove leading /
                        
                        # Leer archivo
                        with open(file_path, 'rb') as fp:
                            file_data = fp.read()
                            
                        email = Message(
                            subject=f"Nuevo Documento Generado: {os.path.basename(file_path)}",
                            sender="no-reply@ticketia.com", 
                            recipients=[business_profile.email],
                            body=f"Hola {business_profile.business_name},\n\nAquí tienes el documento generado desde tu última captura en WhatsApp.\n\nSaludos,\nTu Agente IA."
                        )
                        email.attach(
                            filename=os.path.basename(file_path),
                            content_type="application/pdf",
                            data=file_data
                        )
                        mail_service.send(email)
                        msg_text += "\n\n📧 También te lo he enviado a tu correo."
                        print(f"📧 Email enviado a {business_profile.email}.")
                        
                    except Exception as e:
                        print(f"❌ Error enviando email: {e}")
                
                return msg_text
            else:
                return "❌ No pude procesar la imagen. Asegúrate de que se ve bien el texto."
        # ------------------------------------------------

        # 1. Guardar Mensaje del Usuario
        HistoryService.save_interaction(
            phone=phone_number,
            role="user",
            content=user_message
        )

        # 2. Reconstruir Contexto
        history = HistoryService.get_recent_history(phone_number, limit=10)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        # 3. Primera llamada a OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        final_content = response_message.content
        
        # 4. Verificar Herramientas
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_output = None

                if function_name == "check_availability":
                    tool_output = CalendarTools.check_availability(
                        date=function_args.get("date"),
                        business_phone=business_profile.user_phone
                    )
                    ActivityLog.log(phone_number, "Calendar Agent", f"Consultada agenda: {function_args.get('date')}")

                elif function_name == "book_appointment":
                    tool_output = CalendarTools.book_appointment(
                        date=function_args.get("date"),
                        time=function_args.get("time"),
                        client_name=function_args.get("client_name"),
                        phone=function_args.get("phone"),
                        business_phone=business_profile.user_phone
                    )
                    ActivityLog.log(phone_number, "Calendar Agent", f"Cita agendada: {function_args.get('client_name')}")

                elif function_name == "create_proposal_from_last_image":
                    # Lógica para recuperar la última imagen y procesarla con Redactor
                    last_ticket = Ticket.query.filter_by(user_phone=phone_number).order_by(Ticket.date.desc()).first()
                    
                    if last_ticket and last_ticket.image_path:
                        from modules.proactive.admin_redactor import AdminAssistantAgent
                        assistant = AdminAssistantAgent()
                        
                        # Ensure static_knowledge is a dict
                        sk = business_profile.static_knowledge or {}
                        if isinstance(sk, str):
                            try: sk = json.loads(sk)
                            except: sk = {}
                            
                        # Pasamos image_path directamente (ej: /static/uploads/xyz.jpg)
                        # El agente ahora sabrá leerlo en local gracias a nuestro fix.
                        pdf_path = assistant.process_image_request(last_ticket.image_path, {
                            "business_name": business_profile.business_name,
                            "phone": business_profile.user_phone,
                            "email": business_profile.email,
                            "sector": sk.get('sector', 'Servicios'), # PASS SECTOR
                            "extra_info": sk
                        })
                        if pdf_path:
                            # --- FIX PERSISTENCIA DB (IMAGEN) ---
                            try:
                                from core.db_models import GeneratedDocument, db
                                print(f"💾 Guardando Presupuesto desde Imagen en DB...")
                                new_doc = GeneratedDocument(
                                    user_phone=phone_number,
                                    file_path=pdf_path,
                                    doc_type='proposal',
                                    client_name="Presupuesto (Imagen)", 
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(new_doc)
                                db.session.commit()
                                print(f"✅ Guardado ID: {new_doc.id}")
                            except Exception as e:
                                db.session.rollback()
                                print(f"❌ Error guardando doc imagen: {e}")

                            tool_output = f"✅ Documento generado de la última imagen: {request.host_url.rstrip('/')}{pdf_path}"
                            ActivityLog.log(phone_number, "Admin Redactor", "Generado presupuesto desde Imagen")
                        else:
                            tool_output = "❌ Hubo un error procesando la imagen."
                    else:
                        tool_output = "❌ No encuentro ninguna imagen reciente subida como ticket."

                elif function_name == "create_proposal_from_text":
                    # Lógica para crear PDF desde datos de texto (Audio/Chat)
                    from modules.proactive.admin_redactor import AdminAssistantAgent
                    
                    # Construir payload de datos
                    data_payload = {
                        "client_name": function_args.get("client_name"),
                        "items": function_args.get("items"),
                        "total": function_args.get("total"),
                        "notes": function_args.get("notes"),
                        "date": datetime.now().strftime('%d/%m/%Y') # Se auto-asigna hoy
                    }
                    
                    assistant = AdminAssistantAgent()
                    
                    # Ensure static_knowledge is a dict
                    sk = business_profile.static_knowledge or {}
                    if isinstance(sk, str):
                        try: sk = json.loads(sk)
                        except: sk = {}
                        
                    pdf_path = assistant.generate_proposal_from_data(data_payload, {
                        "business_name": business_profile.business_name,
                        "phone": business_profile.user_phone,
                        "email": business_profile.email,
                        "sector": sk.get('sector', 'Servicios'), # PASS SECTOR
                        "extra_info": sk
                    })
                    
                    if pdf_path:
                        # --- FIX PERSISTENCIA DB ---
                        try:
                            # Importamos aquí para asegurar el contexto
                            from core.db_models import GeneratedDocument, db
                            
                            print(f"💾 Intentando guardar Doc en DB para: {phone_number}")
                            
                            new_doc = GeneratedDocument(
                                user_phone=phone_number,
                                file_path=pdf_path,
                                doc_type='proposal',
                                client_name=function_args.get("client_name") or "Cliente General",
                                created_at=datetime.utcnow()
                            )
                            db.session.add(new_doc)
                            db.session.commit()
                            
                            print(f"✅ ¡Guardado Exitoso! ID: {new_doc.id}")
                            tool_output = "Se ha generado el documento correctamente. Puedes verlo en la sección Documentos."
                            
                        except Exception as e:
                            db.session.rollback()
                            print(f"❌ Error CRÍTICO guardando en DB: {e}")
                            tool_output = "El PDF se generó físicamente, pero hubo un error guardándolo en tu historial."
                        
                        ActivityLog.log(phone_number, "Admin Redactor", f"Generado presupuesto: {function_args.get('client_name')}")
                    else:
                        tool_output = "❌ Hubo un error generando el PDF físico."

                elif function_name == "generate_marketing_material":
                    prompt_text = function_args.get("prompt")
                    fmt = function_args.get("format")
                    
                    # Capturar datos adicionales para el thread (Branding)
                    empresa = business_profile.business_name
                    logo_path_db = business_profile.logo_path
                    base_url = request.host_url
                    
                    # FUNCIÓN INTERNA PARA EL HILO (Background Worker)
                    def _async_marketing_worker(user_phone, prompt, format_type, host_url, p_business_name, p_logo_path, context_app, p_channel): # Pass channel
                        with context_app.app_context(): # Use app context
                            try:
                                print(f"🧵 Thread: Iniciando generación background para {user_phone} via {p_channel}...")
                                
                                # 1. Instanciar Agente (importación diferida para evitar ciclos)
                                from modules.proactive.marketing_agent import MarketingAgent
                                agent = MarketingAgent()
                                
                                # 2. Generar Contenido (Esto tarda 15-30s)
                                file_path = agent.generate_marketing_content(prompt, format_type, business_name=p_business_name, logo_path=p_logo_path)
                                
                                if file_path:
                                    # Save to DB
                                    try:
                                        from core.db_models import GeneratedDocument, db as local_db
                                        new_doc = GeneratedDocument(
                                            user_phone=user_phone,
                                            file_path=file_path,
                                            doc_type='video_prompt' if format_type == 'video' else ('image' if format_type == 'image' else 'presentation')
                                        )
                                        local_db.session.add(new_doc)
                                        local_db.session.commit()
                                    except Exception as e:
                                        print(f"Error saving GeneratedDocument (Thread): {e}")

                                    # 3. Notificar según Canal
                                    if not file_path.startswith('http'):
                                         file_path = f"{host_url.rstrip('/')}{file_path}"
                                    
                                    if p_channel == 'whatsapp':
                                        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
                                        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
                                        client = Client(account_sid, auth_token)
                                        
                                        to_number = user_phone if user_phone.startswith('+') else f"whatsapp:+34{user_phone}"
                                        if "whatsapp:" in user_phone:
                                            to_number = user_phone
                                        else:
                                            to_number = f"whatsapp:{to_number}"

                                        msg_body = "🎨 ¡Aquí tienes tu diseño!" if format_type == 'image' else "📊 ¡Presentación lista!"
                                        if format_type == 'video': msg_body = "🎬 ¡Estrategia de Vídeo Lista!"
                                        
                                        client.messages.create(
                                            from_="whatsapp:+14155238886",
                                            to=to_number,
                                            body=f"{msg_body}\n{file_path}",
                                            media_url=[file_path]
                                        )
                                        print(f"🧵 Thread: ✅ Enviado a {user_phone} (WhatsApp)")
                                    else:
                                        # WEB: No enviar mensaje proactivo (ya está en Docs).
                                        # Podríamos loguear o enviar socket si tuviéramos
                                        print(f"🧵 Thread: ✅ Guardado para Web. No se envía WhatsApp.")
                                        ActivityLog.log(user_phone, "Marketing Agent", f"Diseño listo en Documentos: {format_type}")

                                else:
                                    print("🧵 Thread: ❌ Falló la generación (path vacío).")
                                    
                            except Exception as e:
                                print(f"🧵 Thread: ❌ Error Crítico: {e}")

                    # LANZAR HILO
                    from flask import current_app
                    app_obj = current_app._get_current_object()

                    thread = threading.Thread(
                        target=_async_marketing_worker, 
                        args=(phone_number, prompt_text, fmt, base_url, empresa, logo_path_db, app_obj, channel) # Pass channel
                    )
                    thread.start()
                    
                    # LOG DE INICIO
                    ActivityLog.log(phone_number, "Marketing Agent", f"Iniciado diseño: {prompt_text[:30]}...")

                    # RESPUESTA INMEDIATA AL CHAT (Para evitar Timeout)
                    tool_output = "⏳ ¡Oído! Me pongo a diseñarlo ahora mismo. Como soy una IA detallista, tardaré unos 20-30 segundos.\n\nSigue con lo tuyo, te mandaré un WhatsApp en cuanto lo tenga listo. 🚀"
                elif function_name == "handle_customer_service":
                    from modules.proactive.post_sales import PostSalesAgent
                    print(f"🛠️ [TOOL CALL] handle_customer_service()")
                    
                    # Usamos el último mensaje del usuario para el contexto, ya que la tool call no tiene todos los detalles
                    last_user_msg = "Quiero devolver un pedido" # Fallback
                    for m in reversed(messages):
                        # Safely access role/content whether it's a dict or an object
                        role = m.get('role') if isinstance(m, dict) else getattr(m, 'role', None)
                        content = m.get('content') if isinstance(m, dict) else getattr(m, 'content', None)
                        
                        if role == 'user':
                            last_user_msg = content
                            break
                            
                    agent = PostSalesAgent()
                    # Pasamos el canal al agente para que sepa cómo responder (Twilio vs Web)
                    resp_text, media_url = agent.handle_inquiry(phone_number, last_user_msg, business_profile, channel=channel)
                    
                    # El agente ya se encargó de enviar los adjuntos vía NotifierService si era necesario
                    tool_output = resp_text

                else:
                    tool_output = "Error: Herramienta desconocida."
                
                # Añadir el resultado de la herramienta al historial
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output
                })

                # --- OPTIMIZACIÓN ASYNC (Marketing) ---
                # Si acabamos de lanzar un hilo de generación de imagen, no necesitamos que la IA vuelva a pensar.
                # Devolvemos directamente el mensaje de "Estoy en ello" para responder rápido al usuario y evitar timeouts.
                if function_name == "generate_marketing_material":
                    # Guardamos la interacción para que conste en el historial
                    HistoryService.save_interaction(phone_number, "assistant", tool_output)
                    return tool_output

            
            # 5. Segunda llamada a OpenAI (con el resultado de la herramienta)
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            final_content = final_response.choices[0].message.content
            
        # 6. Guardar Respuesta Final del Asistente
        # (Si hubo tools, guardamos el resultado final. Si no, la respuesta directa)
        if final_content:
            HistoryService.save_interaction(
                phone=phone_number,
                role="assistant",
                content=final_content
            )

        return final_content

    except Exception as e:
        print(f"Error Agente: {e}")
        return "⚠️ Lo siento, tuve un problema interno procesando tu solicitud."
