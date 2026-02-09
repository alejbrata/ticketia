import os
import json
import base64
from fpdf import FPDF
from openai import OpenAI
from datetime import datetime

class AdminAssistantAgent:
    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def classify_image_intent(self, image_url, user_text=""):
        """
        Determina si la imagen es un GASTO (Ticket/Factura recibida)
        o un BORRADOR (Nota/Servilleta para crear un documento).
        """
        try:
            print(f"🧠 Clasificando imagen: {image_url[:15]}...")
            
            # --- PREPARAR IMAGEN (Local vs URL) ---
            image_content = []
            if image_url.startswith(('http://', 'https://')):
                image_content = [{"type": "image_url", "image_url": {"url": image_url}}]
            else:
                # Local Path logic
                try:
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    rel_path = image_url.lstrip('/') 
                    local_path = os.path.join(base_dir, rel_path)
                    
                    with open(local_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        image_content = [{
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }]
                except Exception as e:
                    print(f"⚠️ Error cargando imagen local para clasificación: {e}")
                    # Fallback tentativo, aunque probablemente falle si es local path
                    image_content = [{"type": "image_url", "image_url": {"url": image_url}}]

            prompt = f"""
            Eres un experto clasificador visual para "Ticketia".
            Clasifica la imagen en UNA de dos categorías:
            
            A) 'receipt': SOLO si ves un TICKET TÉRMICO DE CAJA (supermercado, restaurante) o una FACTURA IMPRESA FORMAL. Debe parecer un documento final de pago.
            
            B) 'draft': Para TODO lo demás.
            - Notas manuscritas (papel, cuaderno, servilleta).
            - Dibujos o esquemas con precios.
            - Hojas de pedido manuales.
            - Pantallas de ordenador o fotos de otros dispositivos.
            - Cualquier cosa que NO sea claramente un ticket de compra final.
            
            CONTEXTO EXTRA: "{user_text}"
            (Si el usuario pide presupuesto, cotización, o dice "hazme", ES DRAFT).
            
            SI NO ESTÁS 100% SEGURO QUE ES UN TICKET TÉRMICO/OFICIAL -> CLASIFICA COMO 'draft'.
            
            Responde JSON estricto: {{"type": "receipt" | "draft"}}
            """

            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}] + image_content
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=50
            )
            data = json.loads(response.choices[0].message.content)
            result = data.get('type', 'receipt')
            print(f"   -> Clasificación (v3 Aggressive): {result.upper()} | Context: {user_text}")
            return result
        except Exception as e:
            print(f"❌ Error Clasificación: {e}")
            return "receipt" # Default seguro

    def process_image_request(self, image_url, user_context):
        """
        Orquesta el flujo: Imagen -> Datos Estructurados -> PDF -> Path
        """
        print(f"📄 AdminRedactor: Procesando imagen... {image_url[:20]}...")
        
        # 1. Vision API: Extraer datos (Pasamos contexto sectorial)
        extracted_data = self._analyze_image_with_vision(image_url, extra_context=user_context)
        if not extracted_data:
            return None
            
        # 2. Generar PDF
        pdf_path = self._generate_professional_pdf(extracted_data, user_context)
        return pdf_path

    def generate_proposal_from_data(self, data, user_context):
        """
        Genera PDF directamente desde datos estructurados (sin imagen).
        Útil para comandos de voz/texto.
        """
        print(f"📄 AdminRedactor: Generando PDF desde datos texto...")
        return self._generate_professional_pdf(data, user_context)

    def _analyze_image_with_vision(self, image_url, extra_context={}):
        """
        Analiza una imagen usando GPT-4o Vision + Contexto Sectorial Dinámico (5 Arquetipos).
        """
        # 1. Cargar "Cerebro Sectorial" (Taxonomía Universal)
        sector = str(extra_context.get('sector', 'General')).lower()
        knowledge_file = "type_services.json" # Default seguro (Consultoría/General)
        
        # Mapeo de Palabras Clave a Arquetipos
        keywords = {
            "type_construction.json": ['obra', 'refor', 'const', 'albañ', 'carpin', 'fontan', 'electr', 'pint', 'insta', 'mader', 'metal'],
            "type_retail.json": ['tienda', 'vent', 'comer', 'shop', 'moda', 'ropa', 'alim', 'frut', 'super', 'panad', 'carn', 'pesc', 'flor'],
            "type_hospitality.json": ['restaur', 'bar', 'cafet', 'hotel', 'hostal', 'cater', 'event', 'boda', 'turis', 'viaj'],
            "type_repair.json": ['taller', 'mecan', 'repar', 'sat', 'tecni', 'auto', 'coche', 'moto', 'bici', 'infor', 'movil'],
            "type_services.json": ['serv', 'consul', 'abog', 'asesor', 'gestor', 'market', 'diseñ', 'salud', 'dent', 'fisio', 'medic', 'vet']
        }
        
        # Algoritmo de clasificación simple
        for file, keys in keywords.items():
            if any(k in sector for k in keys):
                knowledge_file = file
                break
            
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            k_path = os.path.join(base_dir, "modules", "knowledge", knowledge_file)
            with open(k_path, 'r', encoding='utf-8') as f:
                sector_knowledge = f.read()
        except Exception as e:
            print(f"⚠️ Warning: Knowledge file error {e}, using generic.")
            sector_knowledge = "Actúa como experto administrativo general."

        # 2. Preparar Imagen
        image_content = []
        if image_url.startswith(('http://', 'https://')):
            image_content = [{"type": "image_url", "image_url": {"url": image_url}}]
        else:
            # Local logic...
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            rel_path = image_url.lstrip('/') 
            local_path = os.path.join(base_dir, rel_path)
            try:
                with open(local_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    image_content = [{
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }]
            except FileNotFoundError:
                return None

        # 3. Prompt Dinámico (RAG Ligero)
        prompt = f"""
        ACTUAR COMO: Experto administrativo en el sector: {sector}.
        CONOCIMIENTO ESPECÍFICO DEL SECTOR:
        {sector_knowledge}
        
        TAREA: Extraer datos de este documento (borrador, nota o foto) para crear un presupuesto formal.
        
        REGLAS DE EXTRACCIÓN CRÍTICAS:
        1. Identifica items y cantidades usando el vocabulario del sector (ej: m2, kg, horas).
        2. Si no hay precio unitario pero sí total, calcúlalo.
        3. "masiva" o "+iva" = Precio base (impuestos excluidos).
        4. "iva incluido" = Desglosar hacia atrás.
        
        OUTPUT JSON:
        {{
            "client_name": "Nombre inferido o 'Cliente Contado'",
            "date": "dd/mm/yyyy",
            "items": [
                {{
                    "desc": "Descripción técnica detallada",
                    "qty": 1,
                    "unit_price": 100.00,
                    "total_line": 100.00
                }}
            ],
            "notes": "Notas sobre pago o plazos"
        }}
        """

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}] + image_content
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Error Vision: {e}")
            return None

    def _generate_professional_pdf(self, data, user_context):
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # --- VAT Logic ---
            sector = user_context.get('sector', 'Servicios').lower()
            # Default logic
            vat_rate = 0.21
            if 'restauración' in sector or 'restauracion' in sector:
                vat_rate = 0.10
            elif 'salud' in sector:
                vat_rate = 0.04 # Or 0.0 depending on service, generic 4 for now
                
            # --- Colors & Fonts ---
            pdf.set_text_color(50, 50, 50)
            
            # --- Header ---
            # Company Name (Left)
            pdf.set_font("Arial", 'B', 20)
            pdf.cell(100, 10, user_context.get('business_name', 'Mi Empresa').upper(), ln=0)
            
            # Document Title (Right)
            pdf.set_font("Arial", 'B', 24)
            pdf.set_text_color(100, 100, 100) # Gray
            pdf.cell(0, 10, "PRESUPUESTO", ln=1, align='R')
            
            pdf.ln(5)
            
            # --- Info Grid ---
            pdf.set_text_color(50, 50, 50)
            pdf.set_font("Arial", '', 10)
            
            # Left Column (Issuer)
            extra = user_context.get('extra_info', {})
            issuer_info = [
                f"Tel: {user_context.get('phone', '')}",
                f"Email: {user_context.get('email', '')}",
                f"NIF: {extra.get('nif', '')}",
                f"Sede: {extra.get('address', '')}"
            ]
            
            top_y = pdf.get_y()
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(90, 5, "DE:", ln=1)
            pdf.set_font("Arial", '', 10)
            for line in issuer_info:
                if line.split(": ")[1]: # Only print if value exists
                    pdf.cell(90, 5, line, ln=1)
            
            # Right Column (Client & Date)
            pdf.set_xy(110, top_y)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, "PARA:", ln=1)
            pdf.set_xy(110, pdf.get_y())
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, f"Cliente: {data.get('client_name', 'Cliente Contado')}", ln=1)
            
            pdf.set_xy(110, pdf.get_y() + 2)
            pdf.cell(0, 5, f"Fecha: {data.get('date') or datetime.now().strftime('%d/%m/%Y')}", ln=1)
            pdf.cell(0, 5, f"Ref: B-{int(datetime.now().timestamp())}", ln=1)
            
            pdf.ln(20)
            
            # --- Table Header ---
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "DESCRIPCIÓN", 0, 0, 'L', 1)
            pdf.cell(20, 10, "CANT", 0, 0, 'C', 1)
            pdf.cell(30, 10, "PRECIO UNIT", 0, 0, 'R', 1)
            pdf.cell(30, 10, "TOTAL", 0, 1, 'R', 1)
            
            # --- Table Body ---
            pdf.set_font("Arial", '', 10)
            
            subtotal = 0.0
            
            # Helper to sanitize text for FPDF (Latin-1)
            def clean_text(text):
                if not text: return ""
                # Replace common symbols not in Latin-1
                text = str(text).replace("€", "EUR").replace("–", "-").replace("—", "-")
                # Encode to Latin-1, replacing errors with ?
                try:
                    return text.encode('latin-1', 'replace').decode('latin-1')
                except:
                    return str(text)

            for item in data.get('items', []):
                desc = str(item.get('desc', 'Item'))
                qty = float(item.get('qty', 1))
                # Support both keys: 'unit_price' (Vision) and 'price' (Tools Schema)
                price = float(item.get('unit_price') or item.get('price') or 0)
                
                # Recalculate line total to ensure consistency
                line_total = qty * price
                subtotal += line_total
                
                # Line drawing
                pdf.cell(100, 8, clean_text(desc), "B")
                pdf.cell(20, 8, f"{int(qty) if qty.is_integer() else qty}", "B", 0, 'C')
                pdf.cell(30, 8, f"{price:,.2f} EUR", "B", 0, 'R')
                pdf.cell(30, 8, f"{line_total:,.2f} EUR", "B", 1, 'R')
                
            pdf.ln(5)
            
            # --- Totals Calculation ---
            vat_amount = subtotal * vat_rate
            total_final = subtotal + vat_amount
            
            # --- Totals Box ---
            # Move to right
            pdf.set_x(110)
            pdf.set_font("Arial", '', 10)
            pdf.cell(50, 6, "Subtotal (Base Imponible):", 0, 0, 'R')
            pdf.cell(30, 6, f"{subtotal:,.2f} EUR", 0, 1, 'R')
            
            pdf.set_x(110)
            pdf.cell(50, 6, f"IVA ({int(vat_rate*100)}%):", 0, 0, 'R')
            pdf.cell(30, 6, f"{vat_amount:,.2f} EUR", 0, 1, 'R')
            
            pdf.set_x(110)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(230, 255, 230) # Light Green
            pdf.cell(50, 10, "TOTAL A PAGAR:", 0, 0, 'R', 1)
            pdf.cell(30, 10, f"{total_final:,.2f} EUR", 0, 1, 'R', 1)
            
            # --- Footer ---
            pdf.ln(15)
            pdf.set_x(10)
            pdf.set_font("Arial", 'I', 9)
            pdf.set_text_color(100, 100, 100)
            notes = data.get('notes', 'Gracias por su confianza. Presupuesto válido por 15 días.')
            pdf.multi_cell(0, 5, f"Notas: {notes}\nEl precio final incluye los impuestos aplicables.")
            
            # Save
            filename = f"budget_{int(datetime.now().timestamp())}.pdf"
            save_dir = os.path.join("static", "generated_docs")
            os.makedirs(save_dir, exist_ok=True)
            full_path = os.path.join(save_dir, filename)
            
            pdf.output(full_path)
            print(f"✅ PDF Generado: {full_path}")
            
            # Return Web URL
            return f"/static/generated_docs/{filename}"
            
        except Exception as e:
            print(f"❌ Error FPDF: {e}")
            return None
