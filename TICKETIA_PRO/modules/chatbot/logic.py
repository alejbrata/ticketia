import os
from openai import OpenAI
from core.db_models import BusinessProfile


def generate_response(user_msg: str, user_phone: str) -> str:
    """
    Genera una respuesta usando el System Prompt configurado en BusinessProfile.
    Busca el perfil por user_phone (identificador principal en la PWA).
    """
    profile = BusinessProfile.query.filter_by(user_phone=user_phone).first()

    if not profile or not profile.system_prompt:
        return "El asistente no está configurado. Por favor completa el asistente en Ajustes."

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{profile.system_prompt}\n\n"
                        f"[GUARDRAIL]: Tu único propósito es ayudar con el negocio "
                        f"{profile.business_name}. Si te preguntan sobre deportes, "
                        f"recetas o política, responde educadamente que solo puedes "
                        f"atender consultas sobre {profile.business_name}."
                    )
                },
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generate_response: {e}")
        return "Lo siento, hubo un error al procesar tu consulta."
