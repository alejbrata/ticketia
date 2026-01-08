import os
import json
from flask import request
from openai import OpenAI
from core.db_models import Ticket
from modules.agents.tools import CalendarTools, TOOLS_SCHEMA
from modules.agents.history import HistoryService

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(user_message, phone_number, business_profile, media_url=None):
    """
    Ejecuta el ciclo del agente con capacidad de usar herramientas, memoria y visión.
    """
    try:
        if not business_profile.system_prompt:
            return "El asistente no está configurado."

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
                return f"✅ ¡Hecho! Aquí tienes tu documento formalizado:\n{request.host_url.rstrip('/')}{pdf_path}"
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
        messages = [{"role": "system", "content": business_profile.system_prompt}]
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
                        
                        # Pasamos image_path directamente (ej: /static/uploads/xyz.jpg)
                        # El agente ahora sabrá leerlo en local gracias a nuestro fix.
                        pdf_path = assistant.process_image_request(last_ticket.image_path, {
                            "business_name": business_profile.business_name,
                            "phone": business_profile.user_phone,
                            "email": business_profile.email,
                            "extra_info": business_profile.static_knowledge or {}
                        })
                        if pdf_path:
                            tool_output = f"✅ Documento generado de la última imagen: {request.host_url.rstrip('/')}{pdf_path}"
                        else:
                            tool_output = "❌ Hubo un error procesando la imagen."
                    else:
                        tool_output = "❌ No encuentro ninguna imagen reciente subida como ticket."
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
