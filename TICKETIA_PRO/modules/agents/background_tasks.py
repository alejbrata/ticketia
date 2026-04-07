import threading
import os
from flask import current_app
from core.db_models import GeneratedDocument, ActivityLog, db
from core.clients import get_twilio_client

def perform_async_marketing_generation(user_phone, prompt, format_type, host_url, p_business_name, p_logo_path, context_app, p_channel):
    """
    Ejecuta la generación de contenido de marketing en segundo plano para no bloquear
    la respuesta a la petición HTTP.
    """
    with context_app.app_context():
        try:
            print(f"🧵 Thread: Iniciando generación background para {user_phone} via {p_channel}...")
            from modules.proactive.marketing_agent import MarketingAgent
            agent = MarketingAgent()
            
            file_path = agent.generate_marketing_content(prompt, format_type, business_name=p_business_name, logo_path=p_logo_path)
            
            if file_path:
                # Save to DB
                try:
                    doc_type = 'video_prompt' if format_type == 'video' else ('image' if format_type == 'image' else 'presentation')
                    new_doc = GeneratedDocument(
                        user_phone=user_phone,
                        file_path=file_path,
                        doc_type=doc_type
                    )
                    db.session.add(new_doc)
                    db.session.commit()
                except Exception as e:
                    print(f"Error saving GeneratedDocument (Thread): {e}")

                # Notificar WhatsApp solo si el canal original era WhatsApp
                if p_channel == 'whatsapp':
                    client = get_twilio_client()
                    
                    to_number = f"whatsapp:{user_phone}" if "whatsapp:" not in user_phone else user_phone
                    full_url = f"{host_url.rstrip('/')}{file_path}" if not file_path.startswith('http') else file_path

                    msg_body = "🎨 ¡Aquí tienes tu diseño!" if format_type == 'image' else "📊 ¡Presentación lista!"
                    if format_type == 'video': msg_body = "🎬 ¡Estrategia de Vídeo Lista!"
                    
                    client.messages.create(
                        from_="whatsapp:+14155238886",
                        to=to_number,
                        body=f"{msg_body}\n{full_url}",
                        media_url=[full_url]
                    )
                    print(f"🧵 Thread: ✅ Enviado a {user_phone} (WhatsApp)")
                else:
                    print(f"🧵 Thread: ✅ Guardado para Web. No se envía WhatsApp.")
                    ActivityLog.log(user_phone, "Marketing Agent", f"Diseño listo en Documentos: {format_type}")
            else:
                print("🧵 Thread: ❌ Falló la generación (path vacío).")
        except Exception as e:
            print(f"🧵 Thread: ❌ Error Crítico: {e}")

def run_marketing_thread(user_phone, prompt, format_type, host_url, p_business_name, p_logo_path, p_channel):
    """Lanzador del hilo de marketing"""
    app_obj = current_app._get_current_object()
    thread = threading.Thread(
        target=perform_async_marketing_generation, 
        args=(user_phone, prompt, format_type, host_url, p_business_name, p_logo_path, app_obj, p_channel)
    )
    thread.start()
