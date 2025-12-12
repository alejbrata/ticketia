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
    """Carga credenciales y devuelve clientes de Sheets y Drive."""
    if not os.path.exists('token.json'):
        raise Exception("❌ Faltan credenciales. Ejecuta 'python setup_auth.py'.")
    
    creds = Credentials.from_authorized_user_file('token.json')
    gc = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gc, drive_service

# --- FUNCIONES DE APILAMIENTO ---
def share_file(drive_service, file_id, email):
    """Comparte un archivo/carpeta con un email específico (Role: Writer)."""
    try:
        user_permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        drive_service.permissions().create(
            fileId=file_id,
            body=user_permission,
            fields='id',
        ).execute()
        print(f"✅ Recurso {file_id} compartido con {email}")
        return True
    except Exception as e:
        print(f"❌ Error compartiendo: {e}")
        return False

def get_or_create_master(gc):
    """Obtiene la hoja Database o la crea si no existe."""
    master_name = "Ticketia-Master"
    try:
        sh = gc.open(master_name)
    except gspread.SpreadsheetNotFound:
        print(f"⚠️ Creando Database '{master_name}'...")
        sh = gc.create(master_name)
        # Cabeceras: Telefono | Email | Sheet_ID | Folder_ID | Estado
        sh.sheet1.append_row(["Phone", "Email", "Sheet_ID", "Folder_ID", "Status"])
    return sh.sheet1

# --- CORE LOGIC: GESTIÓN DE USUARIOS ---
def resolve_user_state(phone, message_body):
    """
    Máquina de estados del usuario.
    Retorna: (dict_contexto, mensaje_respuesta)
    Contexto incluye: state, sheet_id, folder_id, etc.
    """
    gc, drive_service = get_services()
    master = get_or_create_master(gc)
    
    clean_phone = str(phone).replace("whatsapp:", "").replace("+", "")
    
    # 1. Buscar usuario en Master
    # CORRECCIÓN: En gspread v6+, .find() devuelve None si no existe, NO lanza error.
    cell = master.find(clean_phone)
    
    if cell is None:
        # ESCENARIO A: Usuario NUEVO
        print(f"🆕 Nuevo registro: {clean_phone}")
        # Append: Phone | "" | "" | "" | WAITING_EMAIL
        master.append_row([clean_phone, "", "", "", "WAITING_EMAIL"])
        return {"state": "NEW"}, "👋 ¡Bienvenido a Ticketia! Para crear tu contabilidad privada y segura, necesito que me escribas tu **correo de Gmail**."

    else:
        # Usuario YA EXISTE -> Leemos sus datos
        row_num = cell.row
        user_data = master.row_values(row_num)
        # Rellenar con vacíos si la fila está incompleta
        user_data += [""] * (5 - len(user_data))
        
        # [Phone, Email, Sheet_ID, Folder_ID, Status]
        status = user_data[4]

        # 2. Máquina de Estados
        if status == "WAITING_EMAIL":
            # ESCENARIO B: Esperando Email -> Provisioning
            email_candidate = message_body.strip()
            
            if "@" in email_candidate and "." in email_candidate: # Validación básica
                # Nota: Twilio no muestra mensajes intermedios fácilmente sin async, pero procesamos:
                
                try:
                    print(f"⏳ Configurando cuenta para {email_candidate}...")
                    
                    # 1. Crear Carpeta
                    folder_meta = {
                        'name': f"Ticketia - {clean_phone}",
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    folder = drive_service.files().create(body=folder_meta, fields='id').execute()
                    folder_id = folder.get('id')
                    
                    # 2. Crear Sheet
                    sh = gc.create(f"Gastos - {clean_phone}")
                    sheet_id = sh.id
                    
                    # Mover sheet a la carpeta (Drive API)
                    file = drive_service.files().get(fileId=sheet_id, fields='parents').execute()
                    previous_parents = ",".join(file.get('parents'))
                    drive_service.files().update(fileId=sheet_id, addParents=folder_id, removeParents=previous_parents).execute()
                    
                    # 3. Inicializar Sheet
                    sh.sheet1.append_row(["Fecha", "Comercio", "Categoría", "Concepto", "Total", "Evidencia (Drive)"])
                    
                    # 4. COMPARTIR (Privacy First)
                    share_file(drive_service, folder_id, email_candidate)
                    share_file(drive_service, sheet_id, email_candidate)
                    
                    # 5. Actualizar Master
                    # Cols: 1:Phone 2:Email 3:Sheet_ID 4:Folder_ID 5:Status
                    master.update_cell(row_num, 2, email_candidate)
                    master.update_cell(row_num, 3, sheet_id)
                    master.update_cell(row_num, 4, folder_id)
                    master.update_cell(row_num, 5, "ACTIVE")
                    
                    return {"state": "JUST_ACTIVATED"}, "✅ ¡Cuenta configurada! Te he enviado una invitación a tu correo para acceder a tu Excel. Ahora, mándame un ticket."
                    
                except Exception as e:
                    print(f"❌ Error provisioning: {e}")
                    return {"state": "ERROR"}, "❌ Hubo un error creando tu cuenta. Intenta de nuevo más tarde."
            else:
                return {"state": "WAITING_EMAIL"}, "⚠️ Eso no parece un correo válido. Por favor, necesito un Gmail para continuar."

        elif status == "ACTIVE":
            # ESCENARIO C: Usuario Activo
            return {
                "state": "ACTIVE",
                "sheet_id": user_data[2],
                "folder_id": user_data[3]
            }, None # Sin mensaje de respuesta automática, procedemos a lógica de ticket

    return {"state": "UNKNOWN"}, "Error de estado desconocido."

# --- PROCESAMIENTO DE EVIDENCIA Y OCR ---
def upload_evidence(media_url, folder_id):
    try:
        _, drive_service = get_services()
        response = requests.get(media_url)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_meta = {
            'name': f"ticket_{timestamp}.jpg",
            'parents': [folder_id]
        }
        media = MediaIoBaseUpload(io.BytesIO(response.content), mimetype='image/jpeg', resumable=True)
        file = drive_service.files().create(body=file_meta, media_body=media, fields='webViewLink').execute()
        return file.get('webViewLink')
    except Exception as e:
        print(f"❌ Error subida: {e}")
        return None

SYSTEM_PROMPT = """
Eres el motor de OCR de 'Antigravity'.
Responde SOLO con un JSON estricto.
Campos: { "fecha": "DD/MM/YYYY", "comercio": "string", "total": float, "categoria": "string", "concepto": "string" }
Si falla: { "error": "No es un ticket" }.
"""

@app.route("/whatsapp", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    sender = request.values.get('From', 'Unknown')
    
    resp = MessagingResponse()
    
    # 1. Resolver Usuario
    try:
        context, reply_msg = resolve_user_state(sender, incoming_msg)
    except Exception as e:
        print(f"🔥 Critical Error: {e}")
        resp.message("Error interno del servidor.")
        return str(resp)
    
    # Si hay mensaje de respuesta inmediata (Flow de onboarding o error)
    if reply_msg:
        resp.message(reply_msg)
        return str(resp)
    
    # 2. Si es usuario ACTIVO, procesamos ticket
    if context.get("state") == "ACTIVE":
        if num_media > 0:
            media_url = request.values.get('MediaUrl0')
            content_type = request.values.get('MediaContentType0')
            
            if "image" in content_type:
                # A. Backup
                link = upload_evidence(media_url, context["folder_id"])
                
                # B. OCR
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "user", "content": [
                                {"type": "text", "text": SYSTEM_PROMPT},
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
                        # Guardar en SU Sheet
                        gc, _ = get_services()
                        sh = gc.open_by_key(context["sheet_id"]).sheet1
                        fila = [
                            datos.get("fecha"), datos.get("comercio"), 
                            datos.get("categoria"), datos.get("concepto"), 
                            datos.get("total"), link or "Error"
                        ]
                        sh.append_row(fila)
                        resp.message(f"✅ *Guardado*\n🛒 {datos['comercio']}\n💰 {datos['total']}€")
                        
                except Exception as e:
                    print(f"Error AI: {e}")
                    resp.message("⚠️ Error leyendo el ticket.")
            else:
                resp.message("📸 Por favor, envía una foto.")
        else:
            resp.message("👋 Sistema activo. Esperando tickets.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)