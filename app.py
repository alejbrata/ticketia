import os
import json
import io
import datetime
import requests
import gspread
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from openai import OpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv
from pyngrok import ngrok
from difflib import SequenceMatcher

# 1. Cargar secretos
load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Twilio (Mensajes Proactivos)
try:
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    twilio_sender = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
except:
    print("⚠️ AVISO: Faltan credenciales de Twilio en .env")

# Ngrok
ngrok_token = os.getenv("NGROK_AUTHTOKEN")
if ngrok_token:
    ngrok.set_auth_token(ngrok_token)
    print("✅ Token de Ngrok configurado")

# --- CONEXIÓN GOOGLE ---
def get_services():
    if not os.path.exists('token.json'):
        raise Exception("❌ Faltan credenciales.")
    creds = Credentials.from_authorized_user_file('token.json')
    gc = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gc, drive_service

# --- FUNCIONES AUXILIARES ---
def send_whatsapp_push(to_number, body_text):
    try:
        twilio_client.messages.create(from_=twilio_sender, body=body_text, to=to_number)
    except Exception as e:
        print(f"❌ Error Push: {e}")

def share_folder(drive_service, file_id, email):
    try:
        user_permission = {'type': 'user', 'role': 'writer', 'emailAddress': email}
        drive_service.permissions().create(fileId=file_id, body=user_permission, fields='id').execute()
        return True
    except Exception as e:
        print(f"❌ Error compartiendo: {e}")
        return False

def get_or_create_master(gc):
    master_name = "Ticketia-Master"
    try:
        sh = gc.open(master_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(master_name)
        sh.sheet1.append_row(["Phone", "Email", "Sheet_ID", "Folder_ID", "Status"])
    return sh.sheet1

# --- HILO: PROVISIONAMIENTO (ONBOARDING) ---
def onboarding_background(phone, email, row_num, folder_id_existente=None, sheet_id_existente=None):
    print(f"🧵 Hilo Onboarding: Iniciando para {email}...")
    try:
        gc, drive_service = get_services()
        master = get_or_create_master(gc)
        clean_phone = str(phone).replace("whatsapp:", "").replace("+", "")

        # A. MODO ACTUALIZACIÓN
        if folder_id_existente and sheet_id_existente:
            share_folder(drive_service, folder_id_existente, email)
            master.update_cell(row_num, 2, email)
            master.update_cell(row_num, 5, "ACTIVE")
            send_whatsapp_push(phone, "✅ *Correo Actualizado*\nHe dado acceso a tu nueva dirección.")

        # B. MODO CREACIÓN
        else:
            folder_meta = {'name': f"Ticketia - {clean_phone}", 'mimeType': 'application/vnd.google-apps.folder'}
            folder = drive_service.files().create(body=folder_meta, fields='id').execute()
            folder_id = folder.get('id')
            
            share_folder(drive_service, folder_id, email)

            sheet_meta = {'name': f"Gastos - {clean_phone}", 'mimeType': 'application/vnd.google-apps.spreadsheet', 'parents': [folder_id]}
            sheet_file = drive_service.files().create(body=sheet_meta, fields='id').execute()
            sheet_id = sheet_file.get('id')
            
            sh = gc.open_by_key(sheet_id)
            sh.sheet1.append_row(["Fecha", "NIF Emisor", "Comercio", "Categoría", "Concepto", "Base Imponible", "Cuota IVA", "Total", "Evidencia (Drive)"])
            
            master.update_cell(row_num, 2, email)
            master.update_cell(row_num, 3, sheet_id)
            master.update_cell(row_num, 4, folder_id)
            master.update_cell(row_num, 5, "ACTIVE")
            
            send_whatsapp_push(phone, "✅ *¡Cuenta Creada!*\nTe he enviado la invitación.\n📸 *¡Mándame tu primer ticket!*")

    except Exception as e:
        print(f"❌ Error Hilo Onboarding: {e}")
        send_whatsapp_push(phone, "❌ Hubo un error técnico. Escribe 'Hola' para reintentar.")

# --- MÁQUINA DE ESTADOS ---
def resolve_user_state(phone, message_body):
    gc, _ = get_services()
    master = get_or_create_master(gc)
    clean_phone = str(phone).replace("whatsapp:", "").replace("+", "")
    
    cell = master.find(clean_phone)
    msg_clean = message_body.strip()
    
    # 1. USUARIO NUEVO
    if cell is None:
        master.append_row([clean_phone, "", "", "", "WAITING_EMAIL"])
        return {"state": "NEW"}, "👋 ¡Bienvenido a Ticketia! Para configurar tu cuenta, necesito tu **correo de Gmail**."

    # 2. USUARIO EXISTENTE
    row_num = cell.row
    user_data = master.row_values(row_num) + [""] * 5
    status = user_data[4]
    
    if "cambiar correo" in msg_clean.lower():
        master.update_cell(row_num, 5, "WAITING_EMAIL")
        return {"state": "RESET"}, "🔄 Ok, cambiar dirección.\nEscribe tu **NUEVO correo**:"

    # --- FLUJOS ---
    if status == "WAITING_EMAIL":
        if "@" in msg_clean and "." in msg_clean:
            master.update_cell(row_num, 2, msg_clean) 
            master.update_cell(row_num, 5, "VERIFYING_EMAIL")
            return {"state": "VERIFYING"}, f"🧐 Has escrito: **{msg_clean}**\n\n¿Es correcto? (Responde **SÍ** o **NO**)"
        else:
            return {"state": "WAITING"}, "⚠️ Correo no válido. Inténtalo de nuevo."

    elif status == "VERIFYING_EMAIL":
        if msg_clean.lower() in ["si", "sí", "s", "yes", "ok", "correcto"]:
            email_candidato = user_data[1] 
            folder_existente = user_data[3]
            sheet_existente = user_data[2]
            
            return {
                "state": "TRIGGER_ONBOARDING", 
                "email": email_candidato, 
                "row": row_num,
                "folder_id": folder_existente,
                "sheet_id": sheet_existente
            }, "⏳ Genial, dame unos segundos para configurar tu espacio privado..."
        
        else:
            master.update_cell(row_num, 5, "WAITING_EMAIL")
            return {"state": "RETRY"}, "👍 Vale. Escribe de nuevo tu correo correctamente:"

    elif status == "ACTIVE":
        return {"state": "ACTIVE", "sheet_id": user_data[2], "folder_id": user_data[3]}, None

    return {"state": "UNKNOWN"}, "Error de estado."

# --- HILO TICKET (ROBUSTO) ---
def process_ticket_background(media_url, sender, sheet_id, folder_id):
    print("🧵 Hilo Ticket: Procesando...")
    try:
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        prompt = f"""
        Actúa como experto fiscal. HOY ES: {today_str}.
        Analiza la imagen y extrae los datos para el Modelo 303.
        REGLAS:
        1. Si el año es '25' o '24', asume 2025 o 2024.
        2. Devuelve SOLO un objeto JSON válido.
        FORMATO JSON:
        {{
            "fecha": "DD/MM/YYYY",
            "nif": "string",
            "comercio": "string",
            "base": float,
            "iva": float,
            "total": float,
            "categoria": "string",
            "concepto": "string"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": media_url}}]}],
            max_tokens=300
        )
        
        clean_content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        if not clean_content: 
            send_whatsapp_push(sender, "⚠️ La IA no ha podido leer el ticket. Reenvía la foto.")
            return

        datos = json.loads(clean_content)
        
        if "error" in datos:
            send_whatsapp_push(sender, f"⚠️ {datos['error']}")
            return

        gc, drive_service = get_services()
        sh = gc.open_by_key(sheet_id).sheet1

        # Check Duplicados
        rows = sh.get_all_values()[-20:]
        is_dup = False
        if len(rows) > 0:
            new_date = datos.get('fecha')
            try: new_total = float(datos.get('total', 0))
            except: new_total = 0.0
            
            for row in rows:
                if len(row) < 8: continue
                existing_date = row[0]
                try: existing_total = float(str(row[7]).replace("€","").replace(",",".").strip())
                except: existing_total = 0.0
                
                if (existing_date == new_date) and (abs(existing_total - new_total) < 0.01):
                     is_dup = True; break
        
        if is_dup:
            print(f"✋ Duplicado bloqueado: {datos['comercio']}")
            send_whatsapp_push(sender, f"✋ *Ticket Duplicado*\nYa tengo registrado: {datos['comercio']} ({datos['total']}€).")
            return

        # Upload & Save
        resp_img = requests.get(media_url)
        fname = f"ticket_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        media = MediaIoBaseUpload(io.BytesIO(resp_img.content), mimetype='image/jpeg', resumable=False)
        drive_file = drive_service.files().create(body={'name': fname, 'parents': [folder_id]}, media_body=media, fields='webViewLink').execute()
        
        sh.append_row([
            datos.get("fecha"), datos.get("nif", "-"), datos.get("comercio"), 
            datos.get("categoria"), datos.get("concepto"), datos.get("base", 0), 
            datos.get("iva", 0), datos.get("total", 0), drive_file.get('webViewLink')
        ])
        
        print(f"✅ Guardado OK: {datos['comercio']}")
        send_whatsapp_push(sender, f"✅ *Guardado*\n🛒 {datos['comercio']}\n💰 {datos['total']}€")

    except Exception as e:
        print(f"❌ Error CRÍTICO Hilo: {e}")
        send_whatsapp_push(sender, "❌ Error técnico procesando ticket.")

@app.route("/whatsapp", methods=['POST'])
def bot():
    # CHIVATO: Si no ves este mensaje en consola al escribir, revisa Ngrok
    print(f"➡️ Solicitud recibida de: {request.values.get('From')}")
    
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    sender = request.values.get('From', 'Unknown')
    resp = MessagingResponse()
    
    try:
        context, reply_msg = resolve_user_state(sender, incoming_msg)
    except Exception as e:
        print(f"🔥 Error en state: {e}")
        resp.message("Error interno crítico.")
        return str(resp)
    
    if reply_msg:
        resp.message(reply_msg)
        if context.get("state") == "TRIGGER_ONBOARDING":
            threading.Thread(target=onboarding_background, args=(sender, context["email"], context["row"], context["folder_id"], context["sheet_id"])).start()
        return str(resp)
    
    if context.get("state") == "ACTIVE":
        if num_media > 0 and "image" in request.values.get('MediaContentType0', ''):
            resp.message("⏳ *Procesando...*")
            threading.Thread(target=process_ticket_background, args=(request.values.get('MediaUrl0'), sender, context["sheet_id"], context["folder_id"])).start()
        elif "cambiar correo" in incoming_msg:
             pass 
        else:
            resp.message("📸 Manda foto o escribe 'Cambiar correo'.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)