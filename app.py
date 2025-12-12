import os
import json
import io
import datetime
import requests
import gspread
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv
from pyngrok import ngrok
from difflib import SequenceMatcher

# 1. Cargar secretos (.env)
load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ngrok setup
ngrok_token = os.getenv("NGROK_AUTHTOKEN")
if ngrok_token:
    ngrok.set_auth_token(ngrok_token)
    print("✅ Token de Ngrok configurado")
else:
    print("⚠️ AVISO: Falta NGROK_AUTHTOKEN")

# --- CONEXIÓN GOOGLE ---
def get_services():
    if not os.path.exists('token.json'):
        raise Exception("❌ Faltan credenciales. Ejecuta 'python setup_auth.py'.")
    
    creds = Credentials.from_authorized_user_file('token.json')
    gc = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gc, drive_service

# --- FUNCIONES DE APILAMIENTO ---
def share_file(drive_service, file_id, email):
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

# --- CORE LOGIC: GESTIÓN DE USUARIOS ---
def resolve_user_state(phone, message_body):
    gc, drive_service = get_services()
    master = get_or_create_master(gc)
    clean_phone = str(phone).replace("whatsapp:", "").replace("+", "")
    
    cell = master.find(clean_phone)
    
    if cell is None:
        master.append_row([clean_phone, "", "", "", "WAITING_EMAIL"])
        return {"state": "NEW"}, "👋 ¡Bienvenido a Ticketia! Para crear tu contabilidad privada y segura, necesito que me escribas tu **correo de Gmail**."

    else:
        row_num = cell.row
        user_data = master.row_values(row_num) + [""] * 5
        status = user_data[4]

        if status == "WAITING_EMAIL":
            email_candidate = message_body.strip()
            if "@" in email_candidate and "." in email_candidate:
                try:
                    # 1. Crear Carpeta
                    folder_meta = {'name': f"Ticketia - {clean_phone}", 'mimeType': 'application/vnd.google-apps.folder'}
                    folder = drive_service.files().create(body=folder_meta, fields='id').execute()
                    folder_id = folder.get('id')
                    
                    # 2. Crear Sheet
                    sh = gc.create(f"Gastos - {clean_phone}")
                    sheet_id = sh.id
                    
                    # Mover a carpeta
                    file = drive_service.files().get(fileId=sheet_id, fields='parents').execute()
                    drive_service.files().update(fileId=sheet_id, addParents=folder_id, removeParents=",".join(file.get('parents'))).execute()
                    
                    # 3. Inicializar Sheet
                    sh.sheet1.append_row(["Fecha", "Comercio", "Categoría", "Concepto", "Total", "Evidencia (Drive)"])
                    
                    # 4. Compartir
                    share_file(drive_service, folder_id, email_candidate)
                    share_file(drive_service, sheet_id, email_candidate)
                    
                    # 5. Actualizar Master
                    master.update_cell(row_num, 2, email_candidate)
                    master.update_cell(row_num, 3, sheet_id)
                    master.update_cell(row_num, 4, folder_id)
                    master.update_cell(row_num, 5, "ACTIVE")
                    
                    return {"state": "JUST_ACTIVATED"}, "✅ ¡Cuenta configurada! Te he enviado una invitación a tu correo. Ahora, mándame un ticket."
                except Exception as e:
                    print(f"❌ Error provisioning: {e}")
                    return {"state": "ERROR"}, "❌ Error creando tu cuenta."
            else:
                return {"state": "WAITING_EMAIL"}, "⚠️ Necesito un Gmail válido."

        elif status == "ACTIVE":
            return {"state": "ACTIVE", "sheet_id": user_data[2], "folder_id": user_data[3]}, None

    return {"state": "UNKNOWN"}, "Error desconocido."

# --- DRIVE UPLOAD ---
def upload_evidence(media_url, folder_id):
    try:
        _, drive_service = get_services()
        response = requests.get(media_url)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_meta = {'name': f"ticket_{timestamp}.jpg", 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(response.content), mimetype='image/jpeg', resumable=True)
        file = drive_service.files().create(body=file_meta, media_body=media, fields='webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        print(f"❌ Error subida: {e}")
        return None

# --- VALIDACIÓN DUPLICADOS INTELIGENTE ---
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def is_duplicate(sheet, new_data):
    try:
        rows = sheet.get_all_values()
        if len(rows) < 2: return False
        recent_rows = rows[-20:]
        
        new_date = new_data.get('fecha')
        new_merchant = new_data.get('comercio', '').lower()
        try: new_total = float(new_data.get('total', 0.0))
        except: return False
            
        for row in recent_rows:
            if len(row) < 5: continue
            
            existing_date = row[0]
            existing_merchant = row[1].lower()
            try: existing_total = float(str(row[4]).replace("€", "").replace(",", ".").strip())
            except: continue
            
            # 1. Coincidencia Exacta de Fecha y Total
            date_match = (existing_date == new_date)
            total_match = (abs(existing_total - new_total) < 0.01)
            
            # 2. Coincidencia Aproximada de Comercio (>60% similitud)
            # Ej: "El Corte Ingles" vs "CORTE INGLES SA"
            merchant_match = similar(existing_merchant, new_merchant) > 0.6
            
            # DUPLICADO SI: (Fecha + Total) AND (Comercio Similar)
            if date_match and total_match and merchant_match:
                return True
                
        return False
    except Exception as e:
        print(f"⚠️ Error check duplicados: {e}")
        return False

@app.route("/whatsapp", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    sender = request.values.get('From', 'Unknown')
    resp = MessagingResponse()
    
    try:
        context, reply_msg = resolve_user_state(sender, incoming_msg)
    except Exception as e:
        print(f"🔥 Critical Error: {e}")
        resp.message("Error interno.")
        return str(resp)
    
    if reply_msg:
        resp.message(reply_msg)
        return str(resp)
    
    if context.get("state") == "ACTIVE":
        if num_media > 0:
            media_url = request.values.get('MediaUrl0')
            content_type = request.values.get('MediaContentType0')
            
            if "image" in content_type:
                # --- PROMPT CON FECHA DINÁMICA ---
                today_str = datetime.datetime.now().strftime("%d/%m/%Y")
                dynamic_prompt = f"""
                Eres el motor OCR de 'Ticketia'.
                HOY ES: {today_str}.
                
                REGLAS PARA FECHAS:
                1. Si el ticket dice '25' o '24', refiérese al AÑO 2025 o 2024.
                2. Si el año no está claro, usa el año actual ({datetime.datetime.now().year}).
                3. NUNCA inventes fechas.
                
                Responde SOLO JSON:
                {{ "fecha": "DD/MM/YYYY", "comercio": "string", "total": float, "categoria": "string", "concepto": "string" }}
                Si falla: {{ "error": "No es un ticket" }}
                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": dynamic_prompt},
                                {"type": "image_url", "image_url": {"url": media_url}}
                            ]}
                        ],
                        max_tokens=300
                    )
                    clean = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                    datos = json.loads(clean)
                    
                    if "error" in datos:
                        resp.message(f"⚠️ {datos['error']}")
                    else:
                        gc, _ = get_services()
                        sh = gc.open_by_key(context["sheet_id"]).sheet1
                        
                        if is_duplicate(sh, datos):
                            resp.message(f"✋ *Duplicado Detectado*\nYa tengo este ticket de *{datos['comercio']}* ({datos['total']}€).\nNo lo he guardado.")
                        else:
                            link = upload_evidence(media_url, context["folder_id"])
                            fila = [
                                datos.get("fecha"), datos.get("comercio"), 
                                datos.get("categoria"), datos.get("concepto"), 
                                datos.get("total"), link or "Error"
                            ]
                            sh.append_row(fila)
                            resp.message(f"✅ *Guardado*\n🛒 {datos['comercio']}\n📅 {datos['fecha']}\n💰 {datos['total']}€")
                        
                except Exception as e:
                    print(f"Error AI: {e}")
                    resp.message("⚠️ Error leyendo el ticket.")
            else:
                resp.message("📸 Envía una foto.")
        else:
            resp.message("👋 Sistema activo.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)