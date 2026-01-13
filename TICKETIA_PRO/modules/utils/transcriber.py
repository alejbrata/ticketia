import os
import requests
from openai import OpenAI

class AudioTranscriber:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def transcribe(self, media_url):
        """Descarga audio de Twilio y lo transcribe con Whisper."""
        try:
            print(f"🎤 Descargando audio: {media_url}...")
            # Descargar con autenticación de Twilio
            account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
            auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
            resp = requests.get(media_url, auth=(account_sid, auth_token))
            
            if resp.status_code != 200:
                print(f"❌ Error descarga: {resp.status_code}")
                return None

            # Guardar temporalmente
            filename = f"temp_audio_{os.urandom(4).hex()}.ogg"
            with open(filename, 'wb') as f:
                f.write(resp.content)

            # Transcribir con Whisper
            print("   -> Enviando a Whisper...")
            with open(filename, 'rb') as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            
            # Limpieza
            os.remove(filename)
            return transcription.text

        except Exception as e:
            print(f"❌ Error Transcriber: {e}")
            return None
