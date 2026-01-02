import os
import json
import base64
import requests
from datetime import datetime
from openai import OpenAI
from core.db_models import db, Ticket

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_ticket(media_url, user_phone):
    """
    1. Descarga imagen (desde Twilio con Auth).
    2. Convierte a Base64.
    3. Consulta OpenAI.
    4. Guarda en DB.
    """
    try:
        # 1. Descargar imagen de Twilio
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        response = requests.get(media_url, auth=(account_sid, auth_token))
        
        if response.status_code != 200:
            print(f"Error descargando imagen: {response.status_code}")
            return "⚠️ No pude descargar la imagen de Twilio."
            
        # 2. Guardar imagen localmente (para que sea "nuestra")
        import uuid
        filename = f"{uuid.uuid4()}.jpg"
        upload_dir = os.path.join("static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, filename)
        
        # Escribir archivo en disco
        with open(local_path, 'wb') as f:
            f.write(response.content)
            
        # Path relativo para la DB/Web
        db_image_path = f"/static/uploads/{filename}"

        # 3. Convertir a Base64 para OpenAI
        image_data = base64.b64encode(response.content).decode('utf-8')
        media_type = response.headers.get('Content-Type', 'image/jpeg')
        data_url = f"data:{media_type};base64,{image_data}"

        # 4. Prompt para GPT-4o
        prompt = f"""
        Actúa como experto contable español. Extrae datos de este ticket.
        HOY ES: {datetime.now().strftime('%d/%m/%Y')}.
        
        Devuelve JSON ESTRICTO:
        {{
            "fecha": "DD/MM/YYYY",
            "nif": "string",
            "proveedor": "string", 
            "numero_ticket": "string",
            "base": float,
            "iva_percent": float, 
            "cuota_iva": float,
            "total": float,
            "concepto": "resumen corto"
        }}
        Si falta algo, estima o pon null/0.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]}
            ],
            max_tokens=300
        )
        
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # 5. Guardar en DB
        new_ticket = Ticket(
            user_phone=user_phone,
            image_path=db_image_path, # Guardamos la ruta LOCAL y PÚBLICA
            status='processed',
            concept=data.get('concepto', 'Gasto Varios'),
            total=data.get('total', 0.0),
            date=datetime.strptime(data.get('fecha', datetime.now().strftime('%d/%m/%Y')), '%d/%m/%Y'),
            nif=data.get('nif'),
            provider=data.get('proveedor'),
            ticket_number=data.get('numero_ticket'),
            base=data.get('base', 0.0),
            tax_percent=data.get('iva_percent', 0.0),
            fee=data.get('cuota_iva', 0.0),
            raw_data=json.dumps(data)
        )
        
        db.session.add(new_ticket)
        db.session.commit()
        
        return f"✅ Ticket de {data.get('proveedor')} guardado.\n💰 Total: {data.get('total')}€"
        
    except Exception as e:
        print(f"Error procesando ticket: {e}")
        return "⚠️ Error leyendo el ticket. Inténtalo de nuevo."
