import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from flask import Blueprint, request, session, jsonify, Response, stream_with_context, current_app

logger = logging.getLogger(__name__)
from core.db_models import BusinessProfile, db, Notification, GeneratedDocument, LLMCall
from modules.proactive.marketing_agent import MarketingAgent
from modules.agents.background_tasks import run_marketing_thread
from modules.tickets.logic import process_ticket_image
from modules.agents.manager import run_agent
from core.limiter import limiter

api_bp = Blueprint('api', __name__)

# ---------------------------------------------------------------------------
# Marketing / Video
# ---------------------------------------------------------------------------

@api_bp.route('/generate_video_from_image', methods=['POST'])
@limiter.limit("5 per hour")
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
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"video_input_{int(datetime.now().timestamp())}_{file.filename}")
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, filename)
        file.save(local_path)

        # Lanzar en background para no bloquear la petición HTTP (Runway tarda 1-2 min)
        run_marketing_thread(
            user_phone=user_phone,
            prompt="Genera un reel de producto animado y dinámico",
            format_type="video",
            host_url=os.environ.get('PUBLIC_URL', 'http://localhost:5000'),
            p_business_name=profile.business_name,
            p_logo_path=local_path,
        )
        return jsonify({"success": True, "processing": True,
                        "message": "¡En marcha! Te avisaremos cuando el vídeo esté listo en Documentos."})

    except Exception as e:
        logger.error("Error iniciando generación de vídeo: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@api_bp.route('/api/chat', methods=['POST'])
@limiter.limit("30 per minute")
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
        return jsonify({"error": "Perfil no encontrado"}), 404

    response_text = run_agent(
        user_message=user_message,
        phone_number=user_phone,
        business_profile=profile,
    )

    return jsonify({"response": response_text})


# ---------------------------------------------------------------------------
# Tickets & Audio
# ---------------------------------------------------------------------------

@api_bp.route('/upload_web_ticket', methods=['POST'])
@limiter.limit("20 per hour")
def upload_web_ticket():
    if 'user_phone' not in session:
        return jsonify({'error': 'No logueado'}), 401

    if 'ticket' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['ticket']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = f"web_ticket_{int(datetime.now().timestamp())}.jpg"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    user_phone = session['user_phone']
    try:
        result_text = process_ticket_image(filepath, user_phone)
        if result_text.startswith("Error"):
            return jsonify({'error': result_text}), 500
        return jsonify({'success': True, 'message': result_text})
    except Exception as e:
        logger.error("Error procesando ticket imagen: %s", e)
        return jsonify({'error': 'No se pudo procesar la imagen'}), 500


@api_bp.route('/upload_web_audio', methods=['POST'])
@limiter.limit("20 per hour")
def upload_web_audio():
    if 'user_phone' not in session:
        return jsonify({'error': 'No logueado'}), 401

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio'}), 400

    file = request.files['audio']

    # Guardar con extensión adecuada (soporte Safari iOS = mp4/m4a)
    original_name = file.filename or 'audio.webm'
    ext = os.path.splitext(original_name)[1] or '.webm'
    filename = f"web_audio_{int(datetime.now().timestamp())}{ext}"
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)
    logger.info("Audio recibido: %s | tamaño: %d bytes", filename, file_size)

    if file_size < 1000:
        logger.warning("Audio demasiado pequeño (%d bytes), rechazando antes de llamar a Whisper", file_size)
        return jsonify({'error': f'Audio demasiado corto ({file_size} bytes). Habla durante al menos 1 segundo.'}), 400

    from core.clients import get_openai_client
    client = get_openai_client()

    try:
        with open(filepath, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        user_text = transcript.text
        logger.info("Web Audio transcrito: %s...", user_text[:50])

        user_profile = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
        bot_response = run_agent(user_text, session['user_phone'], user_profile)

        return jsonify({'success': True, 'response': bot_response})
    except Exception as e:
        logger.error("Error procesando audio web: %s", e)
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Council (Consejo de Asesores) — SSE streaming
# ---------------------------------------------------------------------------

@api_bp.route('/api/council/stream', methods=['POST'])
@limiter.limit("10 per hour")
def council_stream():
    if 'user_phone' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    topic = data.get('topic', '')

    user_phone = session.get('user_phone')
    user = BusinessProfile.query.filter_by(user_phone=user_phone).first()
    user_context = (
        f"Negocio: {user.business_name}, Sector: {(user.static_knowledge or {}).get('sector', 'General')}"
        if user else "Negocio Genérico"
    )

    import queue as _queue
    import threading as _threading

    event_queue = _queue.Queue()
    _DONE = object()

    def _run_async():
        async def _produce():
            from modules.council.orchestrator import CouncilManager
            manager = CouncilManager()
            # use_mcp=False: el consejo debate con conocimiento LLM, no necesita BD
            async for event in manager.run_session(topic, user_context, use_mcp=False, owner_phone=user_phone):
                event_queue.put(event)
                logger.debug("Council event queued: %s", event.get('type'))

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_produce())
        except Exception as e:
            logger.error("Council _produce error: %s", e)
            event_queue.put({"type": "error", "text": str(e)})
        finally:
            loop.close()
            event_queue.put(_DONE)

    _threading.Thread(target=_run_async, daemon=True).start()

    def generate():
        while True:
            event = event_queue.get()
            if event is _DONE:
                break
            data = json.dumps(event, ensure_ascii=False)
            logger.debug("Council SSE send: %s", event.get('type'))
            yield f"data: {data}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'X-Content-Type-Options': 'nosniff',
        }
    )


# ---------------------------------------------------------------------------
# Web Push — suscripción PWA
# ---------------------------------------------------------------------------

@api_bp.route('/api/push/vapid-public-key', methods=['GET'])
def push_vapid_key():
    """Devuelve la clave pública VAPID para que el frontend pueda suscribirse."""
    key = os.environ.get('VAPID_PUBLIC_KEY', '')
    return jsonify({"publicKey": key})


@api_bp.route('/api/push/subscribe', methods=['POST'])
def push_subscribe():
    """Guarda la PushSubscription del navegador en el perfil del usuario."""
    if 'user_phone' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    subscription = request.get_json()
    if not subscription or 'endpoint' not in subscription:
        return jsonify({"error": "Invalid subscription object"}), 400

    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.push_subscription = json.dumps(subscription)
    db.session.commit()

    logger.info("Push subscription guardada para %s", session['user_phone'])
    return jsonify({"success": True})


@api_bp.route('/api/push/unsubscribe', methods=['POST'])
def push_unsubscribe():
    """Elimina la suscripción push del usuario."""
    if 'user_phone' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = BusinessProfile.query.filter_by(user_phone=session['user_phone']).first()
    if user:
        user.push_subscription = None
        db.session.commit()

    return jsonify({"success": True})


# ---------------------------------------------------------------------------
# LLM Metrics
# ---------------------------------------------------------------------------

@api_bp.route('/api/metrics/llm', methods=['GET'])
def llm_metrics():
    """
    Devuelve métricas agregadas de llamadas LLM para el usuario en sesión.
    Si es admin (user_email == 'admin@ticketia.com') devuelve datos globales.
    """
    if 'user_phone' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    from sqlalchemy import func as sqlfunc
    from datetime import timedelta

    is_admin = session.get('user_email') == 'admin@ticketia.com'
    base_q = LLMCall.query if is_admin else LLMCall.query.filter_by(user_phone=session['user_phone'])

    # ── Hero stats ────────────────────────────────────────────────────────────
    totals = base_q.with_entities(
        sqlfunc.count(LLMCall.id),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.total_tokens), 0),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.cost_usd), 0.0),
        sqlfunc.coalesce(sqlfunc.avg(LLMCall.latency_ms), 0),
        sqlfunc.sum(sqlfunc.cast(LLMCall.success == False, db.Integer)),
    ).one()
    total_calls, total_tokens, total_cost, avg_latency, failed_calls = totals
    success_rate = round((1 - (failed_calls or 0) / max(total_calls, 1)) * 100, 1)

    # ── Por modelo ────────────────────────────────────────────────────────────
    by_model_rows = base_q.with_entities(
        LLMCall.model,
        sqlfunc.count(LLMCall.id),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.total_tokens), 0),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.cost_usd), 0.0),
        sqlfunc.coalesce(sqlfunc.avg(LLMCall.latency_ms), 0),
    ).group_by(LLMCall.model).all()

    by_model = [
        {"model": r[0], "calls": r[1], "tokens": r[2],
         "cost_usd": round(r[3], 5), "avg_latency_ms": round(r[4])}
        for r in by_model_rows
    ]

    # ── Por stage ─────────────────────────────────────────────────────────────
    by_stage_rows = base_q.with_entities(
        LLMCall.stage,
        sqlfunc.count(LLMCall.id),
        sqlfunc.coalesce(sqlfunc.avg(LLMCall.latency_ms), 0),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.cost_usd), 0.0),
    ).group_by(LLMCall.stage).order_by(sqlfunc.count(LLMCall.id).desc()).all()

    by_stage = [
        {"stage": r[0], "calls": r[1],
         "avg_latency_ms": round(r[2]), "cost_usd": round(r[3], 5)}
        for r in by_stage_rows
    ]

    # ── Llamadas por día (últimos 14 días) ───────────────────────────────────
    since = datetime.now(timezone.utc) - timedelta(days=14)
    daily_rows = base_q.filter(LLMCall.created_at >= since).with_entities(
        sqlfunc.date(LLMCall.created_at),
        sqlfunc.count(LLMCall.id),
        sqlfunc.coalesce(sqlfunc.sum(LLMCall.cost_usd), 0.0),
    ).group_by(sqlfunc.date(LLMCall.created_at)).order_by(sqlfunc.date(LLMCall.created_at)).all()

    daily = [
        {"date": str(r[0]), "calls": r[1], "cost_usd": round(r[2], 5)}
        for r in daily_rows
    ]

    return jsonify({
        "is_admin": is_admin,
        "total_calls": total_calls,
        "total_tokens": int(total_tokens),
        "total_cost_usd": round(float(total_cost), 4),
        "avg_latency_ms": round(float(avg_latency)),
        "success_rate": success_rate,
        "by_model": by_model,
        "by_stage": by_stage,
        "daily": daily,
    })
