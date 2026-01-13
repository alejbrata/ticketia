import os
import requests
import json
from datetime import datetime
from openai import OpenAI
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

class MarketingAgent:
    THEMES = {
        "TECH": {"bg": (15, 23, 42), "title": (56, 189, 248), "text": (226, 232, 240)}, # Slate-900 / Sky-400 / Slate-200
        "ECO": {"bg": (20, 83, 45), "title": (74, 222, 128), "text": (220, 252, 231)},   # Green-900 / Green-400 / Green-100
        "CORPORATE": {"bg": (255, 255, 255), "title": (30, 58, 138), "text": (71, 85, 105)}, # White / Blue-900 / Slate-600
        "LUXURY": {"bg": (0, 0, 0), "title": (212, 175, 55), "text": (250, 250, 250)},   # Black / Gold / White
        "CREATIVE": {"bg": (255, 241, 242), "title": (190, 18, 60), "text": (88, 28, 135)} # Pink-50 / Rose-700 / Purple-900
    }

    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # Configurar rutas de salida
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_folder = os.path.join(self.base_dir, 'static', 'generated_docs')
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_marketing_content(self, prompt_text, content_type="image", business_name="Mi Empresa", logo_path=None):
        """
        Genera contenido creativo.
        content_type: 'image' (DALL-E 3) o 'slide' (PowerPoint).
        """
        print(f"🎨 MarketingAgent: Creando {content_type} sobre: '{prompt_text}' para {business_name}")
        
        if content_type == "image":
            return self._generate_dalle_image(prompt_text, business_name, logo_path)
        elif content_type == "slide":
            return self._generate_pptx_slide(prompt_text, business_name)
        else:
            return None

    def _generate_dalle_image(self, user_prompt, business_name, logo_path=None):
        try:
            # 1. Optimizar prompt para DALL-E usando GPT-4o
            optimized_prompt = self._refine_prompt_for_dalle(user_prompt, business_name)
            print(f"   -> Prompt DALL-E: {optimized_prompt[:50]}...")
            
            # 2. Generar Imagen
            response = self.openai.images.generate(
                model="dall-e-3",
                prompt=optimized_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            
            # 3. Descargar y guardar localmente
            filename = f"marketing_{int(datetime.now().timestamp())}.png"
            local_path = os.path.join(self.output_folder, filename)
            
            img_data = requests.get(image_url).content
            with open(local_path, 'wb') as handler:
                handler.write(img_data)
                
            # 4. Superponer Logo (Si existe)
            if logo_path:
                try:
                    from PIL import Image
                    # Convertir ruta web relativa a absoluta
                    # logo_path suele ser "/static/uploads/logos/..."
                    # self.base_dir está en "modules/proactive/...", subir 3 niveles para llegar a root
                    # Pero self.output_folder ya usa self.base_dir correctamente calculado en __init__
                    # self.base_dir en __init__ es: os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    # Esto apunta a TICKETIA_PRO root.
                    # logo_path empieza con /, quitarlo.
                    abs_logo_path = os.path.join(self.base_dir, logo_path.lstrip('/'))
                    
                    if os.path.exists(abs_logo_path):
                        base_img = Image.open(local_path).convert("RGBA")
                        logo_img = Image.open(abs_logo_path).convert("RGBA")
                        
                        # Resize logo (ej: 20% del ancho)
                        base_w, base_h = base_img.size
                        target_w = int(base_w * 0.20)
                        aspect_ratio = logo_img.width / logo_img.height
                        target_h = int(target_w / aspect_ratio)
                        logo_img = logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        
                        # Posición: Esquina inferior derecha con padding
                        padding = 30
                        pos_x = base_w - target_w - padding
                        pos_y = base_h - target_h - padding
                        
                        # Pegar (usando el mismo logo como máscara para transparencia)
                        base_img.paste(logo_img, (pos_x, pos_y), logo_img)
                        
                        # Guardar (sobreescribir)
                        base_img.save(local_path, format="PNG")
                        print("✅ Logo superpuesto correctamente.")
                    else:
                        print(f"⚠️ Logo no encontrado en fs: {abs_logo_path}")
                except Exception as e_pil:
                    print(f"⚠️ Error procesando logo PIL: {e_pil}")
                
            return f"/static/generated_docs/{filename}"
            
        except Exception as e:
            print(f"❌ Error DALL-E: {e}")
            return None

    def _generate_pptx_slide(self, topic, business_name):
        try:
            # 1. Estructurar contenido COMPLETO + TEMA
            presentation_data = self._get_presentation_structure(topic)
            theme_key = presentation_data.get('theme', 'CORPORATE').upper()
            theme = self.THEMES.get(theme_key, self.THEMES['CORPORATE'])
            
            # 2. Crear PPT
            prs = Presentation()
            
            # --- Slide 1: Título Principal ---
            title_slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(title_slide_layout)
            self._apply_theme(slide, theme) # Aplicar estilos
            
            title = slide.shapes.title
            subtitle = slide.placeholders[1]
            
            title.text = presentation_data.get('title', 'Propuesta')
            # Incluir nombre empresa en subtítulo
            subtitle.text = f"{presentation_data.get('subtitle', '')}\nPropuesto por: {business_name}"
            
            self._style_text(title, theme['title'], bold=True, size=Pt(44))
            self._style_text(subtitle, theme['text'], size=Pt(24))

            # --- Slides de Contenido ---
            for slide_data in presentation_data.get('slides', []):
                bullet_slide_layout = prs.slide_layouts[1] # Título + Bullets
                slide = prs.slides.add_slide(bullet_slide_layout)
                self._apply_theme(slide, theme)
                
                # Título de la Slide
                shapes = slide.shapes
                title_shape = shapes.title
                title_shape.text = slide_data.get('title', 'Detalle')
                self._style_text(title_shape, theme['title'], bold=True, size=Pt(36))
                
                # Cuerpo (Bullets)
                body_shape = shapes.placeholders[1]
                tf = body_shape.text_frame
                tf.word_wrap = True
                # Limpiar texto existente (placeholder)
                tf.clear() 

                points = slide_data.get('points', [])
                if points:
                    # Usar el primer párrafo (que clear() deja vacío pero existente)
                    p = tf.paragraphs[0]
                    p.text = points[0]
                    p.level = 0
                    p.space_after = Pt(10)
                    p.font.color.rgb = RGBColor(*theme['text'])
                    p.font.size = Pt(18)

                    # Añadir el resto
                    for point in points[1:]:
                        p = tf.add_paragraph()
                        p.text = point
                        p.level = 0
                        p.space_after = Pt(10)
                        p.font.color.rgb = RGBColor(*theme['text'])
                        p.font.size = Pt(18)

            # Guardar
            filename = f"presentation_{int(datetime.now().timestamp())}.pptx"
            local_path = os.path.join(self.output_folder, filename)
            prs.save(local_path)
            
            return f"/static/generated_docs/{filename}"
            
        except Exception as e:
            print(f"❌ Error PPTX: {e}")
            return None

    def _apply_theme(self, slide, theme):
        # Fondo
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(*theme['bg'])

    def _style_text(self, shape, rgb, bold=False, size=None):
        if not shape.text_frame: return
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(*rgb)
                if bold: run.font.bold = True
                if size: run.font.size = size

    def _refine_prompt_for_dalle(self, text, business_name):
        sys = """
        Eres un experto en Prompts para DALL-E 3.
        Objetivo: Crear una imagen publicitaria de altísimo impacto visual y estético.
        
        RESTRICCIONES DE TEXTO (STRICT):
        - NO incluyas frases largas, eslóganes ni oraciones.
        - SOLO se permite el Nombre de la Marca o Siglas.
        - El texto debe ser mínimo, elegante e integrado en el diseño.
        - Si duda, mejor SIN texto que con texto ilegible.
        
        INSTRUCCIÓN DE MARCA:
        - Incluye visiblemente la marca: '{business_name}'.
        """
        user_msg = f"Idea del usuario: {text}. Marca: {business_name}. Diseña algo moderno, minimalista y profesional."
        
        resp = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user_msg}]
        )
        return resp.choices[0].message.content

    def _get_presentation_structure(self, topic):
        sys = """
        Eres un Consultor Senior de Negocio experto en storytelling.
        Tu objetivo es crear el GUIÓN DETALLADO para una presentación de alto impacto (5-6 diapositivas).
        
        INPUT: Tema del usuario (ej: "Consultoría Gemini").
        OUTPUT: JSON Estricto con el contenido real.
        
        REGLAS DE CONTENIDO:
        - NO uses frases vacías como "Punto 1". Escribe CONTENIDO REAL y VALIOSO.
        - Cada diapositiva debe tener entre 3 y 5 "points".
        - Los "points" deben ser frases completas y explicativas.
        
        REGLAS DE ESTILO (Theme):
        - Clasifica el tema en: 'TECH', 'ECO', 'CORPORATE', 'LUXURY', 'CREATIVE'.
        
        FORMATO JSON:
        {
            "theme": "TECH",
            "title": "TÍTULO PRINCIPAL ATRACTIVO",
            "subtitle": "Subtítulo que venda la idea",
            "slides": [
                {
                    "title": "1. El Desafío Actual",
                    "points": [
                        "Dato impactante: El 40% del tiempo se pierde en tareas repetitivas.",
                        "La competencia ya está adoptando IA generativa.",
                        "Coste de oportunidad de no innovar."
                    ]
                },
                ...
            ]
        }
        """
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": sys}, {"role": "user", "content": topic}],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Error GPT JSON: {e}")
            return {
                "theme": "CORPORATE",
                "title": "Error",
                "subtitle": "Intenta de nuevo",
                "slides": []
            }
