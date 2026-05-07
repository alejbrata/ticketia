"""
Configura el perfil de Demo Business S.L. en la BD:
- static_knowledge (datos del wizard: sector, tono, horario, FAQ, etc.)
- system_prompt generado para el chatbot IA
Uso: python seed_wizard_config.py
"""
import os
from app import app
from core.db_models import db, BusinessProfile

DEMO_PHONE = os.environ.get("DEMO_PHONE", "+34600000001")

STATIC_KNOWLEDGE = {
    "sector": "Tecnología",
    "tone": "Profesional",
    "schedule": "Lunes a Viernes de 9:00 a 18:00. Fuera de horario respondemos en el siguiente día laborable.",
    "payment_methods": "Transferencia bancaria, tarjeta de crédito/débito, Bizum para importes menores a 500€. Factura con SEPA para proyectos recurrentes.",
    "services": (
        "Desarrollo de chatbots inteligentes con GPT-4o y Claude. "
        "Sistemas RAG sobre documentación corporativa. "
        "Automatización de procesos con IA (facturas, emails, informes). "
        "Fine-tuning y evaluación de modelos LLM. "
        "Consultoría estratégica de adopción de IA generativa."
    ),
    "instructions": (
        "Somos una empresa especializada en soluciones de IA generativa para pymes y startups. "
        "Nuestros proyectos tienen plazos de 3 a 8 semanas según complejidad. "
        "Ofrecemos presupuesto gratuito en menos de 48 horas. "
        "Para proyectos enterprise, el cliente asigna un punto de contacto técnico. "
        "No trabajamos con tecnologías propietarias cerradas: todo lo que entregamos es auditable y exportable."
    ),
    "faq": (
        "¿Cuánto tarda un proyecto? Entre 3 y 8 semanas según el alcance. Un chatbot básico puede estar listo en 2 semanas.\n"
        "¿Necesito infraestructura propia? No. Desplegamos en la nube (AWS/Azure) o en tu servidor si lo prefieres.\n"
        "¿Es segura mi información? Sí. Firmamos NDA, los datos nunca salen de la UE y no se usan para entrenar modelos.\n"
        "¿Puedo integrar con mi software actual? Sí. Nos integramos con cualquier sistema que tenga API REST o webhook.\n"
        "¿Qué pasa si la IA comete errores? Incluimos sistema de feedback y corrección continua durante 90 días post-entrega.\n"
        "¿Ofrecéis formación al equipo? Sí, incluida en todos los paquetes Professional y Enterprise.\n"
        "¿Cómo se mide el éxito? Definimos KPIs al inicio del proyecto (reducción de tiempo, tasa de resolución, etc.).\n"
        "¿Hacéis proyectos para startups con presupuesto limitado? Sí, tenemos el paquete Starter desde 1.500€."
    ),
    "return_policy": (
        "Revisiones ilimitadas durante el desarrollo sin coste adicional. "
        "Garantía de funcionamiento de 90 días tras la entrega. "
        "Si no se alcanzan los KPIs acordados en contrato, devolvemos el 50% del importe. "
        "Cancelación antes del inicio del desarrollo: reembolso total. "
        "Cancelación durante el desarrollo: reembolso proporcional al trabajo no realizado."
    ),
    "delivery_time": (
        "Chatbot básico: 2 semanas. "
        "Sistema RAG: 3-4 semanas. "
        "Automatización de procesos: 4-6 semanas. "
        "Proyecto Enterprise a medida: 6-12 semanas."
    ),
    "warranty_info": (
        "90 días de garantía de funcionamiento incluidos en todos los proyectos. "
        "Corrección de bugs sin coste durante el periodo de garantía. "
        "Soporte prioritario (respuesta en 4h) disponible en plan Enterprise."
    ),
    "support_contact": "contacto@demobusiness.ai | +34 91 000 00 01 | L-V 9:00-18:00",
}

SYSTEM_PROMPT = """
Eres el asistente virtual de Demo Business S.L., empresa especializada en desarrollo de soluciones de inteligencia artificial generativa.
Tu tono debe ser Profesional pero cercano: usa un lenguaje claro, técnico cuando sea necesario, y siempre orientado a resolver las dudas del cliente.

INFORMACION CLAVE:
- Horario: Lunes a Viernes de 9:00 a 18:00. Fuera de horario respondemos en el siguiente dia laborable.
- Pagos aceptados: Transferencia bancaria, tarjeta, Bizum (menos de 500EUR), SEPA para proyectos recurrentes.
- Servicios principales: Chatbots con GPT-4o/Claude, sistemas RAG, automatizacion de procesos con IA, fine-tuning de LLMs, consultoria estrategica.

SOBRE PRECIOS Y PLAZOS:
- Paquete Starter: 1.500EUR — chatbot basico, 1 integracion, soporte 30 dias.
- Paquete Professional: 4.500EUR — RAG + chatbot + 3 integraciones, metricas, soporte 90 dias.
- Paquete Enterprise: desde 12.000EUR — solucion a medida, SLA 99.9%, formacion equipo, soporte anual.
- Consultoria por horas: 150EUR/hora, minimo 10 horas.
- Presupuesto gratuito en menos de 48 horas laborables.

GARANTIAS:
- Revisiones ilimitadas durante el desarrollo.
- Garantia de funcionamiento 90 dias post-entrega.
- Si no se cumplen los KPIs acordados, devolvemos el 50% del importe.

INSTRUCCIONES ESPECIFICAS:
- Si preguntan por un caso de uso concreto, da ejemplos reales de como lo hemos resuelto.
- Si preguntan por precios, indica los paquetes y ofrece siempre un presupuesto gratuito sin compromiso.
- Si no sabes algo tecnico muy especifico, pide que contacten por email o telefono para hablar con un especialista.
- Nunca inventes plazos ni precios fuera de los indicados arriba.

OBJETIVO:
Responder dudas de clientes potenciales y actuales basandote UNICAMENTE en esta informacion.
Si preguntan algo que no sabes, pide amablemente que contacten via email: contacto@demobusiness.ai
""".strip()


def seed():
    with app.app_context():
        user = BusinessProfile.query.filter_by(user_phone=DEMO_PHONE).first()
        if not user:
            print(f"[seed_wizard] ERROR: usuario {DEMO_PHONE} no encontrado. Ejecuta seed_owner.py primero.")
            return

        user.business_name    = "Demo Business S.L."
        user.static_knowledge = STATIC_KNOWLEDGE
        user.system_prompt    = SYSTEM_PROMPT
        user.features         = {**(user.features or {}), "bot_enabled": True}
        db.session.commit()
        print(f"[seed_wizard] Wizard configurado para {DEMO_PHONE}")

        # Re-indexar en pgvector
        try:
            from modules.services.embeddings import ingest_wizard_chunks
            chunks = ingest_wizard_chunks(DEMO_PHONE, STATIC_KNOWLEDGE, SYSTEM_PROMPT)
            print(f"[seed_wizard] {chunks} chunks indexados en pgvector.")
        except Exception as e:
            print(f"[seed_wizard] pgvector no disponible o error: {e}")

        print("[seed_wizard] Listo.")


if __name__ == "__main__":
    seed()
