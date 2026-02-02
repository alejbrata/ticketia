import os
import json
from datetime import datetime
from fpdf import FPDF
from openai import OpenAI
from core.db_models import db, Incident, ActivityLog
from core.config import Config
from core.notifier import NotifierService # <-- NUEVO

class PostSalesAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.notifier = NotifierService() # <-- Instancia el servicio agnóstico

    def handle_inquiry(self, user_phone, user_message, owner_profile, channel='whatsapp'):
        """
        Analiza el mensaje y ejecuta acciones respetando la POLITICA DE EMPRESA.
        """
        # 0. Cargar Configuración de Seguridad
        config = owner_profile.agent_config or {}
        ps_config = config.get("post_sales", {})
        
        # Políticas definidas por el usuario dueño
        forbidden_items = ps_config.get("forbidden_items", []) # Ej: ["calzoncillos", "pendientes"]
        exchange_config = ps_config.get("exchange_policy", {})
        exchange_url = exchange_config.get("url")
        exchange_instructions = exchange_config.get("instructions")
        allow_refunds = ps_config.get("allow_refunds", False) # FIX: Define allow_refunds if missing in original code, assumed from context

        # 1. Análisis de intención + EXTRACCIÓN DE PRODUCTO
        tools_prompt = f"""
        Eres un experto en Atención al Cliente. Tu trabajo es CLASIFICAR el mensaje y detectar el PRODUCTO.
        
        FORMATO RESPUESTA: JSON
        {{
            "intent": "RETOUR" | "EXCHANGE" | "STATUS" | "COMPLAINT" | "GENERAL",
            "product": "nombre del producto identificado o null"
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
                max_tokens=60
            )
            data = json.loads(response.choices[0].message.content)
            intent = data.get("intent", "GENERAL")
            product = data.get("product", "").lower()
        except:
            intent = "GENERAL"
            product = ""

        # 2. Ejecutar Acción con FILTROS DE SEGURIDAD
        response_text = ""
        media_url = None
        
        if "RETOUR" in intent:
            # 🛡️ FILTRO 1: Artículos Prohibidos
            is_forbidden = False
            for bad_item in forbidden_items:
                if bad_item in product:
                    is_forbidden = True
                    break
            
            if is_forbidden:
                response_text = f"🚫 Lo siento, pero por motivos de higiene y política de empresa, NO admitimos devoluciones de artículos como '{product}' (está en nuestra lista de artículos no retornables). No puedo generar la etiqueta de devolución para este caso."
                ActivityLog.log(user_phone, "Post-Venta", f"🛑 Devolución DENEGADA: {product}")
            
            # 🛡️ FILTRO 2: Permisos de Reembolso Automático
            elif not allow_refunds:
                response_text = "📝 He registrado tu solicitud de devolución. Como requiere aprobación manual, un supervisor revisará el caso y te contactará en breve para autorizar el envío."
                self._log_incident(user_phone, "PENDING", "Solicitud Devolución (Requiere Aprobación)", user_message)
                ActivityLog.log(user_phone, "Post-Venta", f"⚠️ Devolución PENDIENTE SUPERVISOR: {product}")
                
            else:
                # ✅ APROBADO: Generar etiqueta
                fake_order_id = f"PED-{int(datetime.now().timestamp())}"
                pdf_path = self._generate_return_label(user_phone, fake_order_id)
                
                if not pdf_path.startswith("http"):
                     media_url = f"{Config.PUBLIC_URL}{pdf_path}"
                else:
                     media_url = pdf_path
                     
                response_text = f"✅ He tramitado tu devolución para el pedido {fake_order_id}.\n\nAquí tienes tu etiqueta de envío. Por favor, pégala en el paquete. 📦"
                
                self._log_incident(user_phone, fake_order_id, "Devolución Aprobada", user_message)
                ActivityLog.log(user_phone, "Post-Venta", f"Generada etiqueta devolución {fake_order_id}")

        elif "EXCHANGE" in intent:
            if exchange_url:
                response_text = f"🔄 Para gestionar un cambio (talla/color), por favor accede a nuestro portal de cambios aquí: {exchange_url}"
                ActivityLog.log(user_phone, "Post-Venta", "Solicitud Cambio -> Enviada URL")
            elif exchange_instructions:
                response_text = f"🔄 {exchange_instructions}"
                ActivityLog.log(user_phone, "Post-Venta", "Solicitud Cambio -> Enviadas Instrucciones")
            else:
                response_text = "🔄 Para realizar un cambio, por favor gestiona primero la devolución del artículo actual y realiza un nuevo pedido con la talla/color correcto."
                ActivityLog.log(user_phone, "Post-Venta", "Solicitud Cambio -> Default")

        elif "STATUS" in intent:
            response_text = "🚚 Tu pedido está en reparto. El conductor está a 3 paradas de tu dirección. Llegará antes de las 14:00."
            ActivityLog.log(user_phone, "Post-Venta", "Consulta estado envío")

        elif "COMPLAINT" in intent:
            self._log_incident(user_phone, "N/A", "Queja", user_message)
            
            # Dynamic Conflict Resolution (SAFE MODE) - Refined
            resolution_prompt = """
            ACT AS: Senior Customer Experience Manager.
            CONTEXT: The user is angry/complaining. You must de-escalate.
            LIMITS: DO NOT promise refunds or monetary compensation immediately.
            
            GOAL:
            1. Validate their feelings (Empathy) - "I understand why you are upset..."
            2. Take ownership - "I will personally oversee this case."
            3. Offer a generic but reassuring next step - "I am escalating this to the priority review team right now."
            
            Tone: Professional, calm, warm, and solution-oriented.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": resolution_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                response_text = response.choices[0].message.content
            except:
                response_text = "Entiendo perfectamente tu malestar. He elevado tu incidencia con prioridad ALTA al equipo de dirección para que te contacten hoy mismo con una solución."

            ActivityLog.log(user_phone, "Post-Venta", "🔴 Queja (Modo Seguro): IA Calma al cliente")
            
        else:
            # Respuesta empática genérica
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Eres un asistente de postventa amable y resolutivo. Responde brevemente."},
                    {"role": "user", "content": user_message}
                ]
            )
            response_text = response.choices[0].message.content

        # --- CAMBIO CRÍTICO: USO DEL NOTIFICADOR ---
        # Si hay adjuntos o queremos notificar proactivamente:
        if media_url:
            # Delegamos el envío al notificador, sin saber si es Twilio o Web
            self.notifier.send(user_phone, response_text, media_url, channel=channel)
            return f"He enviado la etiqueta a tu dispositivo ({channel}).", media_url
        else:
            return response_text, None

    def _generate_return_label(self, phone, order_id):
        """Genera un PDF simple simulando una etiqueta de envío."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="ETIQUETA DE DEVOLUCION PRE-PAGADA", ln=1, align="C")
        
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Referencia: {order_id}", ln=1)
        pdf.cell(200, 10, txt=f"Cliente: {phone}", ln=1)
        pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
        
        pdf.ln(20)
        pdf.set_font("Courier", "B", 20)
        pdf.cell(200, 20, txt="||| |||| || ||||| |||| || |||", ln=1, align="C")
        pdf.cell(200, 10, txt=f"1234-5678-{order_id}", ln=1, align="C")
        
        pdf.ln(20)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 10, "Instrucciones:\n1. Imprima esta hoja.\n2. Péguela en el exterior de la caja.\n3. Entregue el paquete en cualquier punto de recogida.")

        filename = f"return_label_{order_id}.pdf"
        # Ruta absoluta usando __file__ para ubicar static
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
