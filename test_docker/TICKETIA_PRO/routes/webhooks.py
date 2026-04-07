import os
from flask import Blueprint, request, jsonify, session
from twilio.twiml.messaging_response import MessagingResponse
from core.db_models import BusinessProfile, db
from modules.agents.manager import run_agent

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.route('/voice/reject', methods=['POST'])
def reject_voice():
    """Endpoint para rechazar llamadas de voz en números de solo-texto/bot."""
    from twilio.twiml.voice_response import VoiceResponse
    resp = VoiceResponse()
    resp.reject(reason='busy')
    return str(resp)

@webhooks_bp.route('/whatsapp', methods=['POST'])
def bot():
    """
    Router V2: Lógica Multi-Tenant Estricta usando el Patrón Dispatcher.
    """
    from modules.services.whatsapp_dispatcher import WhatsAppWebhookDispatcher
    dispatcher = WhatsAppWebhookDispatcher(request.values)
    return dispatcher.process()

