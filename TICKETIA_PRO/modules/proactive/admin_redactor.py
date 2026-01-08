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
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Contexto usuario: '{user_text}'. Analiza la imagen. ¿Es un 'ticket/factura de compra' (receipt) para contabilidad, o es un 'borrador/nota manuscrita' (draft) para redactar un presupuesto/factura nueva? Responde JSON estricto: {{'type': 'receipt' | 'draft'}}"},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=50
            )
            data = json.loads(response.choices[0].message.content)
            result = data.get('type', 'receipt')
            print(f"   -> Clasificación: {result.upper()}")
            return result
        except Exception as e:
            print(f"❌ Error Clasificación: {e}")
            return "receipt" # Default seguro

    def process_image_request(self, image_url, user_context):
        """
        Orquesta el flujo: Imagen -> Datos Estructurados -> PDF -> Path
        """
        print(f"📄 AdminRedactor: Procesando imagen... {image_url[:20]}...")
        
        # 1. Vision API: Extraer datos
        extracted_data = self._analyze_image_with_vision(image_url)
        if not extracted_data:
            return None
            
        # 2. Generar PDF
        pdf_path = self._generate_professional_pdf(extracted_data, user_context)
        return pdf_path

    def _analyze_image_with_vision(self, image_url):
        """
        Analiza una imagen (URL pública o Path Local) usando GPT-4o Vision.
        """
        image_content = []
        
        # A) Es una URL pública (ej: Twilio Media)
        if image_url.startswith(('http://', 'https://')):
            image_content = [{"type": "image_url", "image_url": {"url": image_url}}]
        
        # B) Es una ruta local (ej: /static/uploads/...)
        else:
            # Construir ruta absoluta del sistema
            # Asumimos que image_url viene como '/static/...'
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # Eliminar slash inicial si existe para usar os.path.join correctamente
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
                print(f"❌ Error: No encuentro el archivo local: {local_path}")
                return None

        prompt = """
        Analiza esta imagen (presupuesto manuscrito o nota).
        Extrae: client_name, date, items (desc, qty, price, total), total.
        Devuelve JSON estricto. Si faltan datos, infiérelos coherentemente.
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
            data = json.loads(response.choices[0].message.content)
            return data
        except Exception as e:
            print(f"❌ Error Vision: {e}")
            return None

    def _generate_professional_pdf(self, data, user_context):
        try:
            pdf = FPDF()
            pdf.add_page()
            
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
            pdf.cell(0, 5, f"Fecha: {data.get('date', datetime.now().strftime('%d/%m/%Y'))}", ln=1)
            pdf.cell(0, 5, f"Ref: B-{int(datetime.now().timestamp())}", ln=1)
            
            pdf.ln(20)
            
            # --- Table Header ---
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(110, 10, "DESCRIPCIÓN", 0, 0, 'L', 1)
            pdf.cell(20, 10, "CANT", 0, 0, 'C', 1)
            pdf.cell(30, 10, "PRECIO", 0, 0, 'R', 1)
            pdf.cell(30, 10, "TOTAL", 0, 1, 'R', 1)
            
            # --- Table Body ---
            pdf.set_font("Arial", '', 10)
            for item in data.get('items', []):
                desc = str(item.get('desc', 'Item'))
                qty = str(item.get('qty', 1))
                price = str(item.get('price', 0))
                total = str(item.get('total', 0))
                
                # Line drawing
                pdf.cell(110, 8, desc, "B")
                pdf.cell(20, 8, qty, "B", 0, 'C')
                pdf.cell(30, 8, f"{price} EUR", "B", 0, 'R')
                pdf.cell(30, 8, f"{total} EUR", "B", 1, 'R')
                
            pdf.ln(5)
            
            # --- Totals ---
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(160, 10, "TOTAL A PAGAR:", 0, 0, 'R')
            pdf.set_fill_color(230, 255, 230) # Light Green
            pdf.cell(30, 10, f"{data.get('total', 0)} EUR", 1, 1, 'R', 1)
            
            # --- Footer ---
            pdf.ln(20)
            pdf.set_font("Arial", 'I', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, f"Notas: {data.get('notes', 'Gracias por su confianza. Presupuesto válido por 15 días.')}")
            
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
