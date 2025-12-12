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

# --- NUEVA CONEXIÓN (Modo Humano) ---
def get_services():
    """
    Carga tus credenciales personales desde token.json.
    Si este archivo no existe, fallará (ya lo has creado con setup_auth.py).
    """
    if not os.path.exists('token.json'):
        raise Exception("❌ Faltan credenciales. Ejecuta 'python setup_auth.py' primero.")
    
    creds = Credentials.from_authorized_user_file('token.json')
    
    # Cliente de Sheets
    gc = gspread.authorize(creds)
    # Cliente de Drive
    drive_service = build('drive', 'v3', credentials=creds)
    
    return gc, drive_service

# --- FUNCIONES DE DRIVE (Backup de Fotos) ---
def save_evidence_to_drive(media_url, phone_number):
    try:
        gc, drive_service = get_services()
        root_folder_id = os.getenv("GOOGLE_CLIENTS_FOLDER_ID")
        
        # Limpieza del teléfono
        clean_phone = str(phone_number).replace("+", "")
        
        # 1. Buscar si ya existe la carpeta del usuario dentro de la Maestra
        query = f"'{root_folder_id}' in parents and name = '{clean_phone}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])

        if not items:
            print(f"📂 Creando carpeta Drive para {clean_phone}...")
            folder_metadata = {
                'name': clean_phone,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [root_folder_id]
            }
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            user_folder_id = folder.get('id')
        else:
            user_folder_id = items[0]['id']

        # 2. Descargar imagen desde Twilio
        response = requests.get(media_url)
        if response.status_code != 200:
            print(f"❌ Error descargando de Twilio: {response.status_code}")
            return None

        # 3. Subir a Drive (Usando TU cuota personal)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"ticket_{timestamp}.jpg"
        
        file_metadata = {
            'name': file_name,
            'parents': [user_folder_id]
        }
        
        # Preparamos el archivo en memoria
        media = MediaIoBaseUpload(io.BytesIO(response.content), mimetype='image/jpeg', resumable=True)
        
        # ¡Subida!
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        link = file.get('webViewLink')
        print(f"✅ Foto subida a Drive: {link}")
        return link

    except Exception as e:
        print(f"❌ Error Drive: {e}")
        return None

# --- FUNCIONES DE SHEETS (Excel y Dashboard) ---
def get_user_sheet(phone_number):
    gc, drive_service = get_services()
    master_sheet_name = os.getenv("GOOGLE_MASTER_SHEET", "Ticketia-Master")
    
    # Abrir Libro Maestro
    try:
        sh = gc.open(master_sheet_name)
    except gspread.SpreadsheetNotFound:
        # Si no existe, lo creamos
        sh = gc.create(master_sheet_name)

    # 1. Gestión del Dashboard (Admin)
    try:
        dashboard = sh.get_worksheet(0)
    except:
        dashboard = sh.add_worksheet(title="Dashboard", rows=100, cols=5)
    
    if not dashboard.acell('A1').value:
        dashboard.append_row(["Usuario (Tel)", "Total Gastado (€)", "Estado"])

    clean_phone = str(phone_number).replace("+", "")
    
    # Si el usuario no está en el Dashboard, lo añadimos con fórmula SUMA
    cell = dashboard.find(clean_phone)
    if not cell:
        # Fórmula: =SUM('34600...'!E:E)
        formula = f"=SUM('{clean_phone}'!E:E)"
        dashboard.append_row([clean_phone, formula, "ACTIVO"])

    # 2. Gestión de la Pestaña del Usuario
    try:
        worksheet = sh.worksheet(clean_phone)
        return worksheet, False
    except gspread.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=clean_phone, rows=1000, cols=10)
        # Cabeceras incluyendo la columna de EVIDENCIA
        worksheet.append_row(["Fecha", "Comercio", "Categoría", "Concepto", "Total", "Evidencia (Drive)"])
        return worksheet, True

# --- CEREBRO IA (OCR) ---
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
    phone_number = sender.replace("whatsapp:", "")
    
    resp = MessagingResponse()
    
    # 1. Preparar Excel (Routing)
    try:
        sheet, is_new_user = get_user_sheet(phone_number)
    except Exception as e:
        print(f"❌ Error Routing: {e}")
        resp.message(f"🐛 Error Técnico: {str(e)}")
        return str(resp)

    # Saludo inicial si es nuevo (y no mandó foto aún)
    if is_new_user and num_media == 0:
        resp.message(f"🆕 ¡Bienvenido! He creado tu pestaña.\nMándame un ticket.")
        return str(resp)

    # 2. Procesar Mensaje
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')
        content_type = request.values.get('MediaContentType0')
        
        if "image" in content_type:
            # A) BACKUP EN DRIVE (Prioridad Legal)
            drive_link = save_evidence_to_drive(media_url, phone_number)
            link_msg = "✅ Foto guardada" if drive_link else "⚠️ Error guardando foto"
            
            # B) LECTURA CON IA
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
                    # Guardar fila en Excel
                    fila = [
                        datos.get("fecha"), 
                        datos.get("comercio"), 
                        datos.get("categoria"), 
                        datos.get("concepto"), 
                        datos.get("total"),
                        drive_link if drive_link else "ERROR SUBIDA" # Columna F
                    ]
                    sheet.append_row(fila)
                    
                    resp.message(f"✅ *Ticket Guardado*\n🛒 {datos['comercio']}\n💰 {datos['total']}€\n📸 {link_msg}")

            except Exception as e:
                print(f"ERROR IA: {e}")
                resp.message("⚠️ No he podido leer ese ticket. Intenta que se vea mejor.")
        else:
            resp.message("⚠️ Envía una imagen, por favor.")
    else:
        if not is_new_user:
            resp.message("👋 Sistema activo. Manda ticket.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)