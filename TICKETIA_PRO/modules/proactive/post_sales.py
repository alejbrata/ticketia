import os
import json
import logging
from datetime import datetime
from fpdf import FPDF
from core.db_models import db, Incident, ActivityLog
from core.config import Config
from modules.services.notification import NotificationService

logger = logging.getLogger(__name__)


class PostSalesAgent:
    def __init__(self):
        from core.clients import get_openai_client
        self.client = get_openai_client()

    def handle_inquiry(self, user_phone, user_message, owner_profile, channel=None):
        """
        Analiza el mensaje y ejecuta acciones respetando la POLITICA DE EMPRESA.
        """
        # 0. Cargar Configuración de Seguridad
        config = owner_profile.agent_config or {}
        ps_config = config.get("post_sales", {})
        
        forbidden_items = ps_config.get("forbidden_items", [])
        exchange_config = ps_config.get("exchange_policy", {})
        exchange_url = exchange_config.get("url")
        exchange_instructions = exchange_config.get("instructions")
        allow_refunds = ps_config.get("allow_refunds", False)

        # 1. Análisis de intención + EXTRACCIÓN DE PRODUCTO
        tools_prompt = f"""
        Eres un experto en Atención al Cliente. Tu trabajo es CLASIFICAR el mensaje y detectar el PRODUCTO.
        
        FORMATO RESPUESTA: JSON
        {{
            "intent": "RETOUR" | "EXCHANGE" | "STATUS" | "COMPLAINT" | "GENERAL",
            "product": "nombre del producto identificado o null",
            "sentiment": "positive" | "neutral" | "angry"
        }}
        
        Reglas:
        - Si quiere devolver algo (reembolso): RETOUR
        - Si quiere cambiar talla o color: EXCHANGE
        - Si pregunta dónde está su pedido: STATUS
        - Si está enfadado/queja: COMPLAINT
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": tools_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                max_tokens=150
            )
            data = json.loads(response.choices[0].message.content)
            intent = data.get("intent", "GENERAL")
            product = data.get("product", "") or ""
            sentiment = data.get("sentiment", "neutral")
            
        except Exception as e:
            logger.warning("PostSales: error clasificando intención: %s", e)
            intent = "GENERAL"
            product = ""
            sentiment = "neutral"

        # 2. Ejecutar Acción con FILTROS DE SEGURIDAD
        response_text = ""
        media_url = None
        
        if "RETOUR" in intent:
            # 🛡️ FILTRO 1: Artículos Prohibidos
            is_forbidden = False
            for bad_item in forbidden_items:
                if bad_item in product.lower():
                    is_forbidden = True
                    break
            
            if is_forbidden:
                response_text = f"🚫 Lo siento, pero por motivos de higiene y política de empresa, NO admitimos devoluciones de artículos como '{product}' (está en nuestra lista de artículos no retornables)."
                ActivityLog.log(user_phone, "Post-Venta", f"🛑 Devolución DENEGADA: {product}")
            
            # 🛡️ FILTRO 2: Permisos de Reembolso Automático
            elif not allow_refunds:
                response_text = "📝 He registrado tu solicitud de devolución. Un supervisor revisará el caso y te contactará en breve."
                self._log_incident(user_phone, "PENDING", "Solicitud Devolución (Requiere Aprobación)", user_message)
                
                # ALERTA AL DUEÑO
                NotificationService.send_in_app(
                    user_phone=owner_profile.user_phone,
                    title="⚠️ Solicitud de Devolución",
                    message=f"El cliente {user_phone} quiere devolver '{product}'. Requiere aprobación manual.",
                    type="alert",
                    link="/incidents" # Futuro dashboard incidencias
                )
                
            else:
                # ✅ APROBADO: Generar etiqueta
                fake_order_id = f"PED-{int(datetime.now().timestamp())}"
                relative_path = self._generate_return_label(user_phone, fake_order_id)
                
                # Construir URL absoluta usando PUBLIC_URL (env var centralizada)
                host = os.environ.get('PUBLIC_URL', 'http://localhost:5000').rstrip('/')
                media_url = f"{host}{relative_path}"
                
                response_text = f"✅ He tramitado tu devolución para el pedido {fake_order_id}.\n\nAquí tienes tu etiqueta de envío. 📦"
                
                self._log_incident(user_phone, fake_order_id, "Devolución Aprobada", user_message)
                ActivityLog.log(user_phone, "Post-Venta", f"Generada etiqueta devolución {fake_order_id}")

        elif "EXCHANGE" in intent:
            if exchange_url:
                response_text = f"🔄 Para gestionar un cambio, accede a nuestro portal: {exchange_url}"
            elif exchange_instructions:
                response_text = f"🔄 {exchange_instructions}"
            else:
                response_text = "🔄 Para cambiar, gestiona la devolución y haz un nuevo pedido."

        elif "STATUS" in intent:
            response_text = "🚚 Tu pedido está en reparto. Llegará antes de las 14:00."

        elif "COMPLAINT" in intent or sentiment == "angry":
            self._log_incident(user_phone, "N/A", "Queja", user_message)
            
            # ALERTA URGENTE AL DUEÑO
            NotificationService.send_in_app(
                user_phone=owner_profile.user_phone,
                title="🚨 CLIENTE ENFADADO",
                message=f"Cliente {user_phone} ha puesto una queja: '{user_message[:50]}...'. Atender URGENTE.",
                type="alert"
            )

            # Respuesta calmada IA
            try:
                prompt = "Actúa como Manager de Experiencia de Cliente. El usuario está enfadado. Calma la situación sin prometer dinero. Sé empático y profesional."
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                response_text = response.choices[0].message.content
            except Exception as e:
                logger.warning("PostSales: error generando respuesta para queja: %s", e)
                response_text = "Entiendo tu malestar. He elevado tu incidencia con prioridad ALTA a dirección."

            ActivityLog.log(user_phone, "Post-Venta", "🔴 Queja: IA Calma al cliente + Alerta Dueño")
            
        else:
            # Respuesta general
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un asistente de postventa amable. Responde brevemente."},
                    {"role": "user", "content": user_message}
                ]
            )
            response_text = response.choices[0].message.content

        return response_text, media_url

    def _generate_return_label(self, phone, order_id):
        """Genera un PDF simple simulando una etiqueta de envío."""
        pdf = FPDF()
        pdf.add_page()
        
        # ... Lógica PDF (Simplificada para no ocupar tanto espacio, mantenemos la original) ...
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="ETIQUETA DE DEVOLUCION", ln=1, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Ref: {order_id}", ln=1)
        pdf.cell(200, 10, txt=f"Cliente: {phone}", ln=1)
        
        filename = f"return_label_{order_id}.pdf"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        save_path = os.path.join(base_dir, "static", "generated_docs", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        pdf.output(save_path)
        
        return f"/static/generated_docs/{filename}"

    def _log_incident(self, phone, order, type, desc):
        try:
            inc = Incident(user_phone=phone, order_id=order, type=type, description=desc)
            db.session.add(inc)
            db.session.commit()
        except Exception as e:
            print(f"Error logging incident: {e}")
