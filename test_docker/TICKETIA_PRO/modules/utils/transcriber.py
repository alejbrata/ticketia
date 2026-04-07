import os
import requests
from openai import OpenAI

class AudioTranscriber:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def transcribe(self, media_url):
        # Generar nombre aleatorio
        filename = f"temp_audio_{os.urandom(4).hex()}.ogg"
        try:
            print(f"🎤 Descargando audio: {media_url}...")
            # Descargar (necesita auth de Twilio si es media segura, o url pública)
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
            
            resp = requests.get(media_url, auth=(account_sid, auth_token))
            
            if resp.status_code != 200:
                print(f"❌ Error descarga: {resp.status_code}")
                return None

            with open(filename, 'wb') as f:
                f.write(resp.content)

            print("   -> Enviando a Whisper...")
            with open(filename, 'rb') as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            return transcription.text

        except Exception as e:
            print(f"❌ Error Transcriber: {e}")
            return None
        
        finally:
            # BLOQUE DE SEGURIDAD: Se ejecuta siempre, haya error o no
            if os.path.exists(filename):
                os.remove(filename)
                print(f"   🧹 Limpieza: {filename} eliminado.")
