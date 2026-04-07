import os
import json
from datetime import datetime
from flask import Blueprint, request, session, jsonify, Response, stream_with_context, current_app
from core.db_models import BusinessProfile, db, Notification
from modules.proactive.marketing_agent import MarketingAgent
from modules.tickets.logic import process_ticket_image
from modules.agents.manager import run_agent

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate_video_from_image', methods=['POST'])
def generate_video_from_image():
    if 'user_phone' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    user_phone = session['user_phone']
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()

    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    try:
        # 1. Guardar imagen temporalmente
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"video_input_{int(datetime.now().timestamp())}_{file.filename}")
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, filename)
        file.save(local_path)
        
        # 2. Llamar al Marketing Agent
        from modules.proactive.marketing_agent import MarketingAgent
        agent = MarketingAgent()
        
        # Generar video (Visual Intelligence + Runway)
        video_url = agent.generate_marketing_content(
            prompt_text="", # El prompt se genera de la imagen
            content_type="video",
            business_name=profile.business_name,
            logo_path=local_path # Pasamos la ruta de la imagen
        )
        
        if video_url:
            # 3. Guardar en Base de Datos (GeneratedDocument)
            # El agente ya guarda el MP4 en disk, necesitamos crear el registro DB
            # generated_marketing_content devuelve URL pública. 
            # Parseamos path relativo para la DB.
            # URL ej: https://.../static/generated_docs/runway_123.mp4
            
            relative_path = "/static/generated_docs/" + os.path.basename(video_url)
            
            new_doc = GeneratedDocument(
                user_phone=user_phone,
                file_path=relative_path,
                doc_type='video_prompt', # Usamos este tipo para que salga en la pestaña Video
                client_name="Video Strategy AI",
                created_at=datetime.utcnow()
            )
            db.session.add(new_doc)
            db.session.commit()

            return jsonify({"success": True, "message": "Video generando...", "url": video_url})
        else:
            return jsonify({"success": False, "error": "Falló la generación"}), 500

    except Exception as e:
        print(f"Error generating video: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/api/chat', methods=['POST'])
def chat_api():
    if 'user_phone' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
         return jsonify({"error": "No message"}), 400

    user_phone = session['user_phone']
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()

    if not profile:
        return jsonify({"response": "Error: Perfil no encontrado."})

    # Run Agent
    # We pass 'web' as channel to optimize responses (no sending WP messages if possible)
    from modules.agents.manager import run_agent
    response_text = run_agent(
        user_message=user_message, 
        phone_number=user_phone, 
        business_profile=profile,
        channel='web'
    )
    
    return jsonify({"response": response_text})





@api_bp.route('/upload_web_ticket', methods=['POST'])
def upload_web_ticket():
    if 'user_phone' not in session: return jsonify({'error': 'No logueado'}), 401
    
    if 'ticket' not in request.files:
        return jsonify({'error': 'No file'}), 400
        
    file = request.files['ticket']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    if file:
        # 1. Guardar archivo
        filename = f"web_ticket_{int(datetime.now().timestamp())}.jpg"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # 2. Procesar
        user_phone = session['user_phone']
        result_text = process_ticket_image(filepath, user_phone)
        
        return jsonify({'success': True, 'message': result_text})

@api_bp.route('/upload_web_audio', methods=['POST'])
def upload_web_audio():
    if 'user_phone' not in session: return jsonify({'error': 'No logueado'}), 401
    
    if 'audio' not in request.files: return jsonify({'error': 'No audio'}), 400
    
    file = request.files['audio']
    
    # 1. Guardar WebM
    filename = f"web_audio_{int(datetime.now().timestamp())}.webm"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # 2. Transcribir (Whisper) Inline
    from core.clients import get_openai_client
    client = get_openai_client()
    
    try:
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        user_text = transcript.text
        print(f"🗣️ Web Audio Transcrito: {user_text}")
        
        # 3. Pasar al Manager (Agentes)
        user_profile = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
        bot_response = run_agent(user_text, session['user_phone'], user_profile)
        
        return jsonify({'success': True, 'response': bot_response})
    except Exception as e:
        print(f"Error web audio: {e}")
        return jsonify({'error': str(e)}), 500
# --- ZONA DE EMERGENCIA PARA TFM (Borrar en producción real) ---
@api_bp.route('/api/council/stream', methods=['POST'])
def council_stream():
    data = request.json
    topic = data.get('topic')
    
    # Get user context
    user_phone = session.get('user_phone')
    user = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    
    # Fake minimal context if no user found (shouldn't happen with auth check)
    user_context = f"Negocio: {user.business_name}, Sector: {user.static_knowledge.get('sector', 'General')}" if user else "Negocio Genérico"

    def generate():
        from modules.council.orchestrator import CouncilManager
        manager = CouncilManager()
        
        for event in manager.run_session(topic, user_context):
            yield f"data: {json.dumps(event)}\n\n"
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

