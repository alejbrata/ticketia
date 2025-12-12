import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# 1. Cargar secretos
load_dotenv()

print("🏁 Iniciando prueba de conexión a Google Sheets...")

# 2. Configurar (Hardcodeamos el nombre del JSON para asegurar)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_file = "ticketia-bot-3b7799d18ac9.json"  # <--- Asegúrate de que tu fichero se llama así

try:
    # Intenta cargar credenciales
    print(f"📂 Leyendo archivo: {creds_file}")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client_gs = gspread.authorize(creds)
    print("✅ Credenciales cargadas y autorizadas.")

    # Intenta abrir la hoja
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Gastos Ticketia")
    print(f"🔍 Buscando hoja: '{sheet_name}'")
    
    sheet = client_gs.open(sheet_name).sheet1
    print("✅ Hoja encontrada.")

    # Intenta escribir
    print("✍️ Intentando escribir fila de prueba...")
    sheet.append_row(["PRUEBA", "TEST", "SCRIPT", "MANUAL", 0.00])
    print("🎉 ¡ÉXITO! Fila escrita correctamente. Revisa tu Excel.")

except Exception as e:
    print("\n" + "="*40)
    print("❌ ERROR FATAL DETECTADO:")
    print(f"Tipo de error: {type(e).__name__}")
    print(f"Mensaje: {e}")
    print("="*40 + "\n")
    
    if "SpreadsheetNotFound" in str(type(e).__name__):
        print("💡 PISTA: El robot no encuentra la hoja.")
        print("1. ¿Has invitado al email: bot-ticketia@ticketia-bot.iam.gserviceaccount.com ?")
        print(f"2. ¿La hoja se llama EXACTAMENTE '{sheet_name}'?")