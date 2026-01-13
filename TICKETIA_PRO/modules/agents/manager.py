import os
import json
from flask import request
from openai import OpenAI
from core.db_models import Ticket
from modules.agents.tools import CalendarTools, TOOLS_SCHEMA
from modules.agents.history import HistoryService

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(user_message, phone_number, business_profile, media_url=None, mail_service=None):
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
                            sender="no-reply@ticketia.com", # Configurar sender real en .env
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
        # (Guardamos lo que acaba de escribir el usuario en la DB)
        HistoryService.save_interaction(
            phone=phone_number,
            role="user",
            content=user_message
        )

        # 2. Reconstruir Contexto (System + Historial Reciente)
        history = HistoryService.get_recent_history(phone_number, limit=10)
        
        # El historial ya incluye el último mensaje del user que acabamos de guardar
        # [System] + [History (Old -> New)]
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        # 3. Primera llamada a OpenAI (con Tools)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        final_content = response_message.content
        
        # 4. Verificar si la IA quiere usar una herramienta
        if response_message.tool_calls:
            # Añadir la intención de la IA al historial en memoria para el loop
            messages.append(response_message)
            
            # Ejecutar cada herramienta solicitada
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                tool_output = None
                
                # Despachador Dinámico (Simple)
                if function_name == "check_availability":
                    tool_output = CalendarTools.check_availability(
                        date=function_args.get("date"),
                        business_phone=business_profile.user_phone
                    )
                elif function_name == "book_appointment":
                    tool_output = CalendarTools.book_appointment(
                        date=function_args.get("date"),
                        time=function_args.get("time"),
                        client_name=function_args.get("client_name"),
                        phone=function_args.get("phone"),
                        business_phone=business_profile.user_phone
                    )
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
                            tool_output = f"✅ Documento generado de la última imagen: {request.host_url.rstrip('/')}{pdf_path}"
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
                        "date": None # Se auto-asigna hoy
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
                         tool_output = f"✅ Documento generado correctamente: {request.host_url.rstrip('/')}{pdf_path}"
                    else:
                         tool_output = "❌ Hubo un error generando el PDF."
                elif function_name == "generate_marketing_material":
                    prompt_text = function_args.get("prompt")
                    fmt = function_args.get("format")
                    
                    # Capturar datos para el thread
                    import threading
                    from twilio.rest import Client
                    
                    # URL base (necesaria porque request context se pierde en el thread)
                    base_url = request.host_url.rstrip('/')
                    target_phone = phone_number
                    empresa = business_profile.business_name  # Capturar nombre
                    logo_path_db = business_profile.logo_path # Capturar logo (si existe)
                    
                    def background_generation(p_text, p_fmt, p_phone, p_base_url, p_business_name, p_logo_path):
                        try:
                            print(f"🧵 Thread Start: Generando {p_fmt} para {p_phone}...")
                            from modules.proactive.marketing_agent import MarketingAgent
                            agent = MarketingAgent()
                            # Pasar nombre de empresa Y Logo
                            file_url = agent.generate_marketing_content(p_text, p_fmt, business_name=p_business_name, logo_path=p_logo_path)
                            
                            if file_url:
                                full_url = f"{p_base_url}{file_url}"
                                msg_body = f"✨ ¡Aquí tienes tu {p_fmt} sobre '{p_text}'! Disfrútalo."
                                
                                # Enviar WhatsApp Proactivo
                                account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
                                auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
                                twilio_client = Client(account_sid, auth_token)
                                
                                # Asegurar formato whatsapp:+
                                to_num = p_phone if p_phone.startswith('whatsapp:') else f"whatsapp:{p_phone}"
                                if not to_num.startswith('whatsapp:+'): 
                                    pass

                                msg = twilio_client.messages.create(
                                    from_="whatsapp:+14155238886",
                                    to=to_num,
                                    body=msg_body,
                                    media_url=[full_url]
                                )
                                print(f"✅ Thread Success: Mensaje enviado SID: {msg.sid}")
                            else:
                                print(f"❌ Thread Error: No se generó file_url")
                        except Exception as e:
                            print(f"❌ Thread Crash: {e}")

                    # Lancer hilo con argumento extra
                    thread = threading.Thread(target=background_generation, args=(prompt_text, fmt, target_phone, base_url, empresa, logo_path_db))
                    thread.start()
                    
                    tool_output = "SYSTEM_OK: El proceso de generación ha comenzado CORRCTAMENTE en segundo plano. Dile al usuario que espere unos 30 segundos y que se lo enviarás por WhatsApp en cuanto esté terminar. NO TE DISCULPES."
                else:
                    tool_output = "Error: Herramienta desconocida."
                
                # Añadir el resultado de la herramienta al historial
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output
                })
            
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
