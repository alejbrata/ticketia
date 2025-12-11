import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/whatsapp', methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').lower()
    num_media = int(request.values.get('NumMedia', 0))
    
    resp = MessagingResponse()
    msg = resp.message()

    if num_media > 0:
        # It's an image
        media_url = request.values.get('MediaUrl0')
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un sistema OCR financiero. Extrae los datos de este ticket o factura y devuélvelos SOLO en formato JSON estricto con estas claves: 'comercio', 'total', 'fecha', 'categoria'. Si la imagen no es un ticket, devuelve un JSON con error."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract data from this image."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": media_url,
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content
            msg.body(result_text)
            
        except Exception as e:
            msg.body(f"Error processing image: {str(e)}")
            
    else:
        # It's text
        msg.body("👋 Soy Antigravity. Mándame una foto de un ticket para procesarlo.")

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
