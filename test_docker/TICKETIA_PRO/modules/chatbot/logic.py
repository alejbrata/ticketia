import os
from openai import OpenAI
from core.db_models import BusinessProfile

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_response(user_msg, phone):
    """Genera respuesta usando el System Prompt configurado en BusinessProfile."""
    # Buscar el perfil asociado al número de teléfono del BOT (o del usuario destino)
    # En app.py pasamos 'target_number' que es el número de whatsapp.
    
    # IMPORTANTE: La lógica de `app.py` busca el `target_business` antes.
    # Pero aquí `generate_response` recibe `phone`. 
    # Dependiendo de cómo `app.py` lo llame.
    # En el código del usuario: `generate_response(incoming_msg, target_number)`
    
    profile = BusinessProfile.query.filter_by(whatsapp_number=phone).first()
    
    if not profile or not profile.system_prompt:
        return "El asistente no está configurado."
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{profile.system_prompt}\n\n[GUARDRAIL]: Tu único propósito es ayudar con el negocio. Si te preguntan sobre deportes, recetas o política, responde educadamente que solo puedes atender consultas sobre {profile.business_name}."},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error IA: {e}"
