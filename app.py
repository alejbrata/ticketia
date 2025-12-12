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
    GESTIÓN HÍBRIDA:
    1. Actualiza el Dashboard (Hoja 0) con el resumen.
    2. Devuelve la Pestaña personal del usuario.
    """
    gc = get_gspread_client()
    master_sheet_name = os.getenv("GOOGLE_MASTER_SHEET", "Ticketia-Master")
    
    # Abrir el Libro Maestro
    try:
        sh = gc.open(master_sheet_name)
    except gspread.SpreadsheetNotFound:
        print(f"⚠️ No encuentro '{master_sheet_name}'. Creándolo...")
        sh = gc.create(master_sheet_name)

    # --- PARTE 1: EL DASHBOARD (Admin) ---
    try:
        dashboard = sh.get_worksheet(0) # Siempre la primera pestaña
    except:
        dashboard = sh.add_worksheet(title="Dashboard", rows=100, cols=5)
    
    # Si está vacía, ponemos cabeceras chulas
    if not dashboard.acell('A1').value:
        dashboard.append_row(["Usuario (Tel)", "Total Gastado (€)", "Estado"])
        # Le damos un poco de formato (negrita) a la primera fila
        dashboard.format('A1:C1', {'textFormat': {'bold': True}})

    clean_phone = str(phone_number).replace("+", "")
    
    # ¿Está este usuario en el Dashboard?
    cell = dashboard.find(clean_phone)
    if not cell:
        print(f"📊 Añadiendo usuario {clean_phone} al Dashboard...")
        # LA FÓRMULA MÁGICA: Suma la columna E de la pestaña del usuario
        # Usamos sintaxis en inglés (=SUM), Google Sheets lo traduce a tu idioma local
        formula = f"=SUM('{clean_phone}'!E:E)"
        dashboard.append_row([clean_phone, formula, "ACTIVO"])

    # --- PARTE 2: LA PESTAÑA DEL USUARIO ---
    try:
        worksheet = sh.worksheet(clean_phone)
        return worksheet, False
    except gspread.WorksheetNotFound:
        print(f"🆕 Creando pestaña personal para: {clean_phone}")
        worksheet = sh.add_worksheet(title=clean_phone, rows=1000, cols=10)
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
    sender = request.values.get('From', 'Unknown') 
    
    # Limpiamos el sender
    phone_number = sender.replace("whatsapp:", "")
    
    resp = MessagingResponse()
    
    # 1. Resolver Usuario y Dashboard
    try:
        sheet, is_new_user = get_user_sheet(phone_number)
    except Exception as e:
        print(f"❌ Error crítico en routing: {e}")
        resp.message(f"🐛 DEBUG: {str(e)}")
        return str(resp)
        
    if is_new_user:
        welcome_msg = f"🆕 ¡Bienvenido! He creado tu pestaña privada.\nMándame una foto para empezar."
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
                
                clean = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
                datos = json.loads(clean)
                
                if "error" in datos:
                    resp.message(f"⚠️ {datos['error']}")
                else:
                    # Guardar fila
                    fila = [datos.get("fecha"), datos.get("comercio"), datos.get("categoria"), datos.get("concepto"), datos.get("total")]
                    sheet.append_row(fila)
                    
                    msg = f"✅ *Guardado*\n🛒 {datos['comercio']}\n💰 {datos['total']}€"
                    if is_new_user: msg = "🆕 ¡Cuenta creada!\n" + msg
                    resp.message(msg)

            except Exception as e:
                print(f"ERROR IA: {e}")
                resp.message("⚠️ No he podido leer ese ticket. Intenta que se vea mejor.")
        else:
            resp.message("⚠️ Por favor, envía una imagen.")
    else:
        if not is_new_user:
            resp.message("👋 Tu sistema de gastos está activo. Envíame un ticket.")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)