import os
import json
import gspread
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from pyngrok import ngrok

# 1. Cargar secretos
load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ngrok setup
ngrok_token = os.getenv("NGROK_AUTHTOKEN")
if ngrok_token:
    ngrok.set_auth_token(ngrok_token)
    print("✅ Token de Ngrok configurado desde .env")
else:
    print("⚠️ AVISO: No he encontrado NGROK_AUTHTOKEN en el .env")

# 2. Configuración Global de Google Sheets
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "ticketia-bot-3b7799d18ac9.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    return gspread.authorize(creds)

def get_user_sheet(phone_number):
    """
    ARQUITECTURA DE PESTAÑAS (TABS):
    En lugar de crear un archivo por usuario, creamos una PESTAÑA por usuario
    dentro del archivo maestro. Esto evita el error de cuota de disco del bot.
    """
    gc = get_gspread_client()
    master_sheet_name = os.getenv("GOOGLE_MASTER_SHEET", "Ticketia-Master")
    
    # 1. Abrir el Libro Maestro (Contenedor)
    try:
        sh = gc.open(master_sheet_name)
    except gspread.SpreadsheetNotFound:
        print(f"⚠️ No encuentro el archivo '{master_sheet_name}'. Creándolo...")
        sh = gc.create(master_sheet_name)
        # Si lo crea el bot, compártelo contigo mismo inmediatamente por la web o fallará la visualización
        
    # 2. Buscar o Crear la Pestaña del Usuario
    # Limpiamos el teléfono para que sea un nombre de hoja válido (sin +)
    clean_phone = str(phone_number).replace("+", "")
    
    try:
        # Intentamos acceder a la pestaña con el nombre del teléfono
        worksheet = sh.worksheet(clean_phone)
        print(f"✅ Pestaña encontrada para: {clean_phone}")
        return worksheet, False
        
    except gspread.WorksheetNotFound:
        # No existe, la creamos
        print(f"🆕 Creando nueva pestaña para: {clean_phone}")
        worksheet = sh.add_worksheet(title=clean_phone, rows=1000, cols=10)
        
        # Le ponemos las cabeceras
        worksheet.append_row(["Fecha", "Comercio", "Categoría", "Concepto", "Total"])
        
        return worksheet, True

# Prompt del sistema
SYSTEM_PROMPT = """
Eres el motor de OCR de 'Antigravity'.
Tu misión: Analizar imágenes de tickets/facturas y extraer datos.
Responde SOLO con un JSON estricto.
Campos: { "fecha": "DD/MM/YYYY", "comercio": "string", "total": float, "categoria": "string", "concepto": "string" }
Si falla: { "error": "No es un ticket" }.
"""

@app.route("/whatsapp", methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    sender = request.values.get('From', 'Unknown') # ej: whatsapp:+34666...
    
    # Limpiamos el sender para quitar 'whatsapp:'
    phone_number = sender.replace("whatsapp:", "")
    
    resp = MessagingResponse()
    
    # 1. Resolver Usuario (Pestañas)
    try:
        sheet, is_new_user = get_user_sheet(phone_number)
    except Exception as e:
        print(f"❌ Error crítico en routing: {e}")
        resp.message(f"🐛 DEBUG: {str(e)}")
        return str(resp)
        
    # Bienvenida si es pestaña nueva
    if is_new_user:
        welcome_msg = f"🆕 ¡Bienvenido! He creado tu pestaña privada en el Excel.\nMándame una foto para estrenarla."
        if num_media == 0:
            resp.message(welcome_msg)
            return str(resp)

    # 2. Procesar Mensaje
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')
        content_type = request.values.get('MediaContentType0')
        
        if "image" in content_type:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": SYSTEM_PROMPT},
                                {"type": "image_url", "image_url": {"url": media_url}}
                            ],
                        }
                    ],
                    max_tokens=300
                )
                
                # Limpieza de JSON
                raw = response.choices[0].message.content
                clean = raw.replace("```json", "").replace("```", "").strip()
                datos = json.loads(clean)
                
                if "error" in datos:
                    resp.message(f"⚠️ {datos['error']}")
                else:
                    # Guardar fila
                    fila = [datos.get("fecha"), datos.get("comercio"), datos.get("categoria"), datos.get("concepto"), datos.get("total")]
                    sheet.append_row(fila)
                    
                    msg = f"✅ *Guardado en tu Pestaña*\n🛒 {datos['comercio']}\n💰 {datos['total']}€"
                    if is_new_user: msg = "🆕 ¡Pestaña creada!\n" + msg
                    resp.message(msg)

            except Exception as e:
                print(f"ERROR: {e}")
                resp.message(f"💥 ERROR: {str(e)}")
        else:
            resp.message("⚠️ Mándame una foto, no un archivo raro.")
    else:
        if not is_new_user:
            resp.message("👋 Todo listo. Tu pestaña de gastos está activa.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)