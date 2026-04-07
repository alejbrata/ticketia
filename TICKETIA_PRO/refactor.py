import os

def create_blueprints():
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Create backups
    os.makedirs("backups", exist_ok=True)
    with open("backups/app.py.bak", "w", encoding="utf-8") as f:
        f.write(content)

    lines = content.split('\n')
    
    # Simple state machine to parse routes
    imports = []
    setup = []
    
    current_section = "setup"
    sections = {
        "setup": [],
        "web": [],
        "api": [],
        "webhooks": [],
        "main": []
    }
    
    def get_section(line, current):
        if line.startswith("if __name__ == '__main__':"):
            return "main"
        if "--- WEBHOOK WHATSAPP" in line:
            return "webhooks"
        if "--- RUTAS WEB" in line:
            return "web"
        if "--- THE COUNCIL ROUTES" in line:
            return "web"
        if "@app.route('/api/" in line or "@app.route('/generate_video" in line or "@app.route('/upload_web" in line:
            return "api"
        if "@app.route('/" in line and current == "api": 
            # Switching back to web
            return "web"
        if "@app.route('/voice/reject" in line:
            return "webhooks"
        if "@app.route('/demo" in line:
            return "web"
        if "@app.route('/setup_magic" in line:
            return "web"
        return current

    # We need to correctly capture the function blocks because of Python's indentation.
    # It's better to split by '@app.route' and then classify each route block.
    
    # Extract headers
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("# --- RUTAS WEB (Frontend) ---"):
            header_end = i
            break
            
    header_lines = lines[:header_end]
    
    # Process blocks
    blocks = content[content.find("# --- RUTAS WEB (Frontend) ---"):].split('@app.route')
    
    api_routes = []
    web_routes = []
    webhook_routes = []
    
    # blocks[0] is just the "# --- RUTAS WEB..." comment
    for block in blocks[1:]:
        route_def = "@app.route" + block
        
        # Determine classification by inspecting the route path
        route_path = block.split("'")[1] if "'" in block.split('\n')[0] else block.split('"')[1]
        
        if route_path.startswith('/api/') or route_path in ['/generate_video_from_image', '/upload_web_ticket', '/upload_web_audio']:
            api_routes.append(route_def.replace('@app.route', '@api_bp.route'))
        elif route_path in ['/whatsapp', '/voice/reject']:
            webhook_routes.append(route_def.replace('@app.route', '@webhooks_bp.route'))
        else:
            web_routes.append(route_def.replace('@app.route', '@web_bp.route'))

    # Separate out the main block from the last route (which has `if __name__ ...` attached at the bottom)
    # The last block appended to web_routes probably contains `if __name__ == '__main__':`
    # Let's clean that up.
    last_block = web_routes[-1]
    main_spliter = "if __name__ == '__main__':"
    if main_spliter in last_block:
        parts = last_block.split(main_spliter)
        web_routes[-1] = parts[0]
        main_block = main_spliter + parts[1]
    else:
        main_block = "if __name__ == '__main__':\n\n    port = int(os.environ.get(\"PORT\", 5000))\n    app.run(host='0.0.0.0', port=port, debug=True)\n"

    # Write webhooks_bp
    webhooks_code = f"""import os
from flask import Blueprint, request, jsonify, session
from twilio.twiml.messaging_response import MessagingResponse
from core.db_models import BusinessProfile, db
from modules.agents.manager import run_agent

webhooks_bp = Blueprint('webhooks', __name__)

{''.join(webhook_routes)}
"""
    with open("routes/webhooks.py", "w", encoding="utf-8") as f:
        f.write(webhooks_code)

    # Write api_bp
    api_code = f"""import os
import json
from datetime import datetime
from flask import Blueprint, request, session, jsonify, Response, stream_with_context
from core.db_models import BusinessProfile, db, Notification
from modules.proactive.marketing_agent import MarketingAgent
from modules.tickets.logic import process_ticket_image
from modules.agents.manager import run_agent

api_bp = Blueprint('api', __name__)

{''.join(api_routes)}
"""
    with open("routes/api.py", "w", encoding="utf-8") as f:
        f.write(api_code)

    # Write web_bp
    web_code = f"""import os
import io
import json
import secrets
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify, render_template, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app import mail # circular, but lazy loading or global works here since mail is initialized
from core.db_models import BusinessProfile, Ticket, ChatMessage, GeneratedDocument, SynergyMatch, ActivityLog, db

web_bp = Blueprint('web', __name__)

{''.join(web_routes)}
"""
    with open("routes/web.py", "w", encoding="utf-8") as f:
        f.write(web_code)

    # Rewrite app.py
    new_app = '\n'.join(header_lines) + "\n\n"
    new_app += "# --- BLUEPRINTS REGISTRATION ---\n"
    new_app += "from routes.web import web_bp\n"
    new_app += "from routes.api import api_bp\n"
    new_app += "from routes.webhooks import webhooks_bp\n\n"
    new_app += "app.register_blueprint(web_bp)\n"
    new_app += "app.register_blueprint(api_bp)\n"
    new_app += "app.register_blueprint(webhooks_bp)\n\n"
    new_app += main_block
    
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(new_app)

    print("Refactoring complete.")

if __name__ == "__main__":
    create_blueprints()
