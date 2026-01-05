import os
import json
from openai import OpenAI
from modules.agents.tools import CalendarTools, TOOLS_SCHEMA

# Inicializar cliente OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_agent(user_message, phone_number, business_profile):
    """
    Ejecuta el ciclo del agente con capacidad de usar herramientas.
    """
    try:
        if not business_profile.system_prompt:
            return "El asistente no está configurado."

        # 1. Preparar Historial Mensajes
        messages = [
            {"role": "system", "content": business_profile.system_prompt},
            {"role": "user", "content": user_message}
        ]

        # 2. Primera llamada a OpenAI (con Tools)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # 3. Verificar si la IA quiere usar una herramienta
        if response_message.tool_calls:
            # Añadir la intención de la IA al historial
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
                else:
                    tool_output = "Error: Herramienta desconocida."
                
                # Añadir el resultado de la herramienta al historial
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_output
                })
            
            # 4. Segunda llamada a OpenAI (con el resultado de la herramienta)
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            return final_response.choices[0].message.content
            
        else:
            # No hubo tools, devolver respuesta directa
            return response_message.content

    except Exception as e:
        print(f"Error Agente: {e}")
        return "⚠️ Lo siento, tuve un problema interno procesando tu solicitud."
