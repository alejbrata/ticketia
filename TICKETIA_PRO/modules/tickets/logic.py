import os
import json
import logging
import base64
from datetime import datetime
from openai import OpenAI
from core.db_models import db, Ticket

logger = logging.getLogger(__name__)

_TICKET_PROMPT = """
Actúa como experto contable español. Extrae datos de este ticket.
HOY ES: {today}.

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

def _parse_ticket_date(fecha_str):
    """Parsea fecha DD/MM/YYYY con fallback seguro a hoy."""
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(fecha_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.now()


def _build_openai_client():
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def process_ticket_image(file_path, user_phone):
    """
    Procesa un ticket subido desde la web (PWA).
    file_path: Ruta absoluta local del archivo ya guardado.
    """
    client = _build_openai_client()

    try:
        with open(file_path, "rb") as image_file:
            content = image_file.read()

        # Detectar tipo MIME real por cabecera de bytes
        if content[:3] == b'\xff\xd8\xff':
            media_type = 'image/jpeg'
        elif content[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = 'image/png'
        elif content[:4] == b'%PDF':
            media_type = 'application/pdf'
        else:
            media_type = 'image/jpeg'  # fallback

        image_data = base64.b64encode(content).decode('utf-8')
        data_url = f"data:{media_type};base64,{image_data}"

        prompt = _TICKET_PROMPT.format(today=datetime.now().strftime('%d/%m/%Y'))

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

        raw = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"proveedor": "Unknown", "total": 0.0}

        # Calcular ruta relativa para la DB
        if 'static' in file_path:
            rel_path = file_path.split('static')[-1].replace('\\', '/')
            db_image_path = f"/static{rel_path}"
        else:
            db_image_path = f"/static/uploads/{os.path.basename(file_path)}"

        new_ticket = Ticket(
            user_phone=user_phone,
            image_path=db_image_path,
            status='processed',
            concept=data.get('concepto', 'Gasto Web'),
            total=data.get('total', 0.0),
            date=_parse_ticket_date(data.get('fecha', '')),
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

        return f"Ticket de {data.get('proveedor', 'Desconocido')} ({data.get('total', 0)}€) guardado."

    except Exception as e:
        logger.error("Error process_ticket_image: %s", e)
        return f"Error procesando imagen: {e}"
