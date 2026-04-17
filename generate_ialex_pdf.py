"""
Genera el PDF de conocimiento corporativo de IAlex Solutions
para probar el pipeline RAG de Zeptai/Ticketia.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT = "ialex_solutions_knowledge_base.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    rightMargin=2.5*cm, leftMargin=2.5*cm,
    topMargin=2.5*cm, bottomMargin=2.5*cm,
    title="IAlex Solutions — Base de Conocimiento Corporativo",
    author="IAlex Solutions"
)

styles = getSampleStyleSheet()

# Estilos personalizados
h1 = ParagraphStyle("h1", parent=styles["Heading1"],
    fontSize=20, textColor=colors.HexColor("#4F46E5"),
    spaceAfter=10, spaceBefore=20)
h2 = ParagraphStyle("h2", parent=styles["Heading2"],
    fontSize=14, textColor=colors.HexColor("#6D28D9"),
    spaceAfter=6, spaceBefore=14)
h3 = ParagraphStyle("h3", parent=styles["Heading3"],
    fontSize=11, textColor=colors.HexColor("#1E293B"),
    spaceAfter=4, spaceBefore=10)
body = ParagraphStyle("body", parent=styles["Normal"],
    fontSize=10, leading=15, alignment=TA_JUSTIFY, spaceAfter=6)
bullet = ParagraphStyle("bullet", parent=styles["Normal"],
    fontSize=10, leading=14, leftIndent=14, spaceAfter=3)
caption = ParagraphStyle("caption", parent=styles["Normal"],
    fontSize=8, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)
cover_title = ParagraphStyle("cover_title", parent=styles["Normal"],
    fontSize=30, textColor=colors.HexColor("#4F46E5"),
    alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=8)
cover_sub = ParagraphStyle("cover_sub", parent=styles["Normal"],
    fontSize=14, textColor=colors.HexColor("#6D28D9"),
    alignment=TA_CENTER, spaceAfter=4)
cover_body = ParagraphStyle("cover_body", parent=styles["Normal"],
    fontSize=10, textColor=colors.HexColor("#475569"),
    alignment=TA_CENTER, spaceAfter=4)

story = []

# ── PORTADA ──────────────────────────────────────────────────────────────────
story.append(Spacer(1, 3*cm))
story.append(Paragraph("IAlex Solutions", cover_title))
story.append(Paragraph("Base de Conocimiento Corporativo", cover_sub))
story.append(Spacer(1, 0.5*cm))
story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#4F46E5"), hAlign="CENTER"))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Documento interno para uso del Asistente IA", cover_body))
story.append(Paragraph("Versión 1.0 — Abril 2026", cover_body))
story.append(Spacer(1, 4*cm))
story.append(Paragraph(
    "Confeccionar presupuestos · Atender clientes · Resolver dudas técnicas",
    cover_sub))
story.append(PageBreak())

# ── 1. PRESENTACIÓN DE LA EMPRESA ────────────────────────────────────────────
story.append(Paragraph("1. Presentación de la empresa", h1))
story.append(Paragraph(
    "IAlex Solutions es una consultora boutique fundada en 2023, especializada en el diseño, "
    "desarrollo e implantación de soluciones de Inteligencia Artificial Generativa para pymes y "
    "medianas empresas. Con sede en Madrid (España) y clientes en toda la Unión Europea, "
    "acompañamos a organizaciones en su transformación digital poniendo la IA al servicio de sus "
    "procesos de negocio.", body))
story.append(Paragraph(
    "Nuestra misión es democratizar la IA generativa, haciendo que tecnologías antes reservadas "
    "a grandes corporaciones sean accesibles, comprensibles y rentables para cualquier empresa.", body))
story.append(Paragraph("Datos de contacto:", h3))
data_contact = [
    ["Web", "www.ialex-solutions.com"],
    ["Email comercial", "hola@ialex-solutions.com"],
    ["Soporte técnico", "soporte@ialex-solutions.com"],
    ["Teléfono", "+34 910 123 456"],
    ["Dirección", "Calle Gran Vía 42, 3.ª planta, 28013 Madrid"],
    ["Horario de atención", "Lunes a viernes, 9:00–18:00 (CET)"],
    ["CIF", "B-87654321"],
]
t = Table(data_contact, colWidths=[5*cm, 10*cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EEF2FF")),
    ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#4F46E5")),
    ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("PADDING", (0,0), (-1,-1), 6),
]))
story.append(t)
story.append(Spacer(1, 0.3*cm))

# ── 2. CATÁLOGO DE SERVICIOS Y TARIFAS ───────────────────────────────────────
story.append(Paragraph("2. Catálogo de servicios y tarifas", h1))

story.append(Paragraph("2.1 Implantación de Agentes IA Conversacionales", h2))
story.append(Paragraph(
    "Diseñamos e implantamos chatbots y asistentes virtuales basados en modelos de lenguaje de última "
    "generación (GPT-4o, Claude 3.5, Gemini 1.5 Pro). El agente aprende del conocimiento interno de "
    "la empresa gracias a RAG (Retrieval-Augmented Generation) y se integra con CRMs, ERPs y "
    "plataformas de mensajería.", body))
data_s1 = [
    ["Modalidad", "Descripción", "Precio (IVA no incl.)"],
    ["Starter", "1 agente, hasta 2 integraciones, 3 meses soporte", "2.500 €"],
    ["Business", "Hasta 3 agentes, integraciones ilimitadas, 6 meses soporte", "6.000 €"],
    ["Enterprise", "Agentes multimodales + RAG avanzado, SLA 24/7", "Desde 15.000 €"],
    ["Mantenimiento mensual", "Actualizaciones de modelos, monitorización, soporte", "Desde 350 €/mes"],
]
t2 = Table(data_s1, colWidths=[4*cm, 8*cm, 3.5*cm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4F46E5")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("ALIGN", (2,0), (2,-1), "RIGHT"),
    ("PADDING", (0,0), (-1,-1), 6),
]))
story.append(t2)

story.append(Paragraph("2.2 Automatización de Procesos con IA Generativa (Gen-AI Ops)", h2))
story.append(Paragraph(
    "Automatizamos flujos de trabajo que implican generación o análisis de texto, imágenes o datos "
    "estructurados: resúmenes de informes, clasificación de documentos, generación de contratos, "
    "análisis de sentimiento de reseñas, etc.", body))
data_s2 = [
    ["Servicio", "Precio orientativo"],
    ["Auditoría de procesos automatizables (1 día)", "800 €"],
    ["Prototipo de automatización (2 semanas)", "3.500 €"],
    ["Implementación completa + formación", "Desde 8.000 €"],
    ["Precio por 1.000 documentos procesados (producción)", "Desde 12 €"],
]
t3 = Table(data_s2, colWidths=[10*cm, 5.5*cm])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#6D28D9")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("ALIGN", (1,0), (1,-1), "RIGHT"),
    ("PADDING", (0,0), (-1,-1), 6),
]))
story.append(t3)

story.append(Paragraph("2.3 Formación y Talleres Corporativos", h2))
story.append(Paragraph(
    "Programas de upskilling para equipos que quieran entender y usar la IA generativa en su día a día. "
    "Disponibles en modalidad presencial (Madrid) o remota.", body))
data_s3 = [
    ["Taller", "Duración", "Precio por grupo (hasta 12 personas)"],
    ["Introducción a la IA Generativa", "4 h", "900 €"],
    ["Prompt Engineering Avanzado", "8 h", "1.600 €"],
    ["IA para Marketing y Contenidos", "6 h", "1.200 €"],
    ["Construye tu Agente IA (técnico)", "16 h (2 días)", "3.200 €"],
    ["Formación a medida", "A definir", "Consultar presupuesto"],
]
t4 = Table(data_s3, colWidths=[5.5*cm, 2.5*cm, 7.5*cm])
t4.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#059669")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("PADDING", (0,0), (-1,-1), 6),
]))
story.append(t4)

story.append(Paragraph("2.4 Consultoría Estratégica de IA", h2))
story.append(Paragraph(
    "Sesiones de consultoría para directivos y responsables de transformación digital. "
    "Analizamos el estado actual, identificamos casos de uso con mayor ROI potencial y "
    "diseñamos la hoja de ruta de adopción de IA.", body))
story.append(Paragraph("• Sesión diagnóstico inicial (2 h): 400 € (deducible si contratas un proyecto)", bullet))
story.append(Paragraph("• Hoja de ruta IA (entregable en 5 días hábiles): 2.200 €", bullet))
story.append(Paragraph("• Consultoría bajo retainer mensual: desde 1.500 €/mes", bullet))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph("2.5 Desarrollo de Aplicaciones IA a Medida", h2))
story.append(Paragraph(
    "Construimos desde cero aplicaciones web, móviles o de escritorio que incorporan capacidades "
    "de IA generativa: desde buscadores semánticos internos hasta plataformas multiagente. "
    "Usamos frameworks modernos (LangChain, LlamaIndex, Semantic Kernel) y desplegamos en AWS, "
    "Azure o GCP.", body))
story.append(Paragraph("• Tarifa hora/consultor senior IA: 95 €/h", bullet))
story.append(Paragraph("• Proyectos llave en mano: presupuesto cerrado tras análisis (mínimo 10.000 €)", bullet))
story.append(Paragraph("• Bolsa de horas flexible (prepago): 20 h = 1.700 € · 50 h = 4.000 € · 100 h = 7.500 €", bullet))

story.append(PageBreak())

# ── 3. PROCESO DE TRABAJO ─────────────────────────────────────────────────────
story.append(Paragraph("3. Nuestro proceso de trabajo", h1))
story.append(Paragraph(
    "Seguimos una metodología ágil adaptada a proyectos de IA que garantiza entregas incrementales "
    "y alineamiento continuo con el cliente:", body))
fases = [
    ("1. Discovery (1–2 semanas)",
     "Reuniones con stakeholders, mapeo de procesos, análisis de datos disponibles, "
     "definición de KPIs de éxito y entregables."),
    ("2. Prototipo / PoC (2–4 semanas)",
     "Construcción de un prototipo funcional que valida la viabilidad técnica y el valor "
     "de negocio antes de comprometer presupuesto completo."),
    ("3. Desarrollo e integración (4–12 semanas)",
     "Desarrollo iterativo en sprints de 2 semanas. Integración con sistemas existentes "
     "(CRM, ERP, BBDD, APIs). Tests de calidad y seguridad."),
    ("4. Despliegue y formación (1–2 semanas)",
     "Puesta en producción, documentación técnica y funcional, formación al equipo del cliente."),
    ("5. Soporte y evolución (continuo)",
     "Monitorización de modelos, actualización de prompts y embeddings, nuevas funcionalidades "
     "según roadmap acordado."),
]
for titulo, desc in fases:
    story.append(Paragraph(titulo, h3))
    story.append(Paragraph(desc, body))

# ── 4. PREGUNTAS FRECUENTES (FAQ) ─────────────────────────────────────────────
story.append(Paragraph("4. Preguntas frecuentes", h1))

faqs = [
    ("¿Qué modelos de IA utilizáis?",
     "Trabajamos principalmente con GPT-4o y GPT-4o-mini de OpenAI, Claude 3.5 Sonnet de Anthropic "
     "y Gemini 1.5 Pro de Google. Para clientes con requisitos de privacidad estrictos también "
     "desplegamos modelos open-source (Llama 3, Mistral) en infraestructura privada."),
    ("¿Mis datos salen de la empresa?",
     "Depende de la solución elegida. Con modelos en la nube (OpenAI, Anthropic) los datos pasan "
     "por sus APIs bajo acuerdo de procesamiento de datos (DPA). Para datos sensibles recomendamos "
     "despliegue on-premise o en nube privada del cliente con modelos open-source."),
    ("¿Cuánto cuesta la IA por uso (tokens)?",
     "El coste de inferencia lo asume el cliente directamente con su propia API key. "
     "Orientativamente, GPT-4o cuesta ~2,50 $/M tokens de entrada y ~10 $/M de salida. "
     "Para la mayoría de pymes el coste mensual es inferior a 50 €."),
    ("¿Necesito infraestructura técnica propia?",
     "No es imprescindible. Podemos gestionar toda la infraestructura en AWS o Azure por una "
     "cuota mensual de hosting incluida en el mantenimiento. Si ya tienes servidores propios, "
     "también podemos desplegar ahí."),
    ("¿Cuánto tarda una implantación típica?",
     "Un agente conversacional Starter puede estar operativo en 3–4 semanas. Un proyecto "
     "Enterprise completo con integraciones complejas puede requerir 3–4 meses."),
    ("¿Ofrecéis prueba gratuita?",
     "Sí. Ofrecemos una demo personalizada de 45 minutos donde mostramos un prototipo "
     "con los datos del cliente. Contacta en hola@ialex-solutions.com para solicitarla."),
    ("¿Tenéis experiencia en mi sector?",
     "Hemos trabajado con clientes en retail, logística, despachos jurídicos, clínicas, "
     "agencias de marketing, inmobiliarias y empresas industriales. Contáctanos para ver "
     "casos de uso específicos de tu sector."),
    ("¿Qué garantías ofrecéis?",
     "Todos los proyectos incluyen periodo de garantía de 30 días post-entrega para corrección "
     "de defectos sin coste adicional. Los contratos de mantenimiento incluyen SLA de respuesta "
     "según nivel contratado (4 h Business, 1 h Enterprise)."),
]
for pregunta, respuesta in faqs:
    story.append(Paragraph(f"<b>{pregunta}</b>", body))
    story.append(Paragraph(respuesta, body))
    story.append(Spacer(1, 0.2*cm))

story.append(PageBreak())

# ── 5. CASOS DE ÉXITO ─────────────────────────────────────────────────────────
story.append(Paragraph("5. Casos de éxito (referencias)", h1))

casos = [
    ("LegalDoc Asesores (Madrid)",
     "Automatización de redacción de contratos laborales y civiles. Reducción del 70% del "
     "tiempo de redacción. El agente genera un borrador en <30 segundos a partir de un formulario "
     "de 10 campos. Proyecto: 18.000 €. ROI estimado: 6 meses."),
    ("Moda Próxima (e-commerce de moda)",
     "Agente conversacional multicanal (web + WhatsApp) para atención al cliente con RAG "
     "sobre catálogo de 12.000 SKUs. Resolución autónoma del 78% de consultas. "
     "Reducción del equipo de atención de 5 a 2 personas en turno de noche."),
    ("Grupo Logístico Serrano",
     "Sistema de extracción automática de datos de albaranes y facturas (multimodal). "
     "Procesamiento de 4.000 documentos/mes con 96% de precisión. Proyecto: 12.000 €."),
    ("Academia Digital Pro (formación online)",
     "Tutor IA personalizado para 3.200 alumnos activos. El asistente resuelve dudas sobre "
     "contenido de cursos con RAG sobre 800 horas de material indexado. NPS post-implantación: 72."),
]
for cliente, descripcion in casos:
    story.append(Paragraph(cliente, h3))
    story.append(Paragraph(descripcion, body))

# ── 6. EQUIPO ──────────────────────────────────────────────────────────────────
story.append(Paragraph("6. Equipo", h1))
equipo = [
    ["Nombre", "Rol", "Especialidad"],
    ["Alejandro Brava", "CEO & AI Architect", "LLMs, sistemas multiagente, estrategia de producto"],
    ["Laura Sánchez", "Lead Engineer", "Python, LangChain, infraestructura cloud (AWS/GCP)"],
    ["Carlos Méndez", "ML Engineer", "Fine-tuning, embeddings, RAG, pgvector"],
    ["Ana Torres", "UX/AI Designer", "Diseño de conversaciones, prompt engineering, UX"],
    ["David Iglesias", "Sales & Partnerships", "Desarrollo de negocio, sector legal y retail"],
]
t_eq = Table(equipo, colWidths=[4.5*cm, 4.5*cm, 6.5*cm])
t_eq.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E293B")),
    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ("PADDING", (0,0), (-1,-1), 6),
]))
story.append(t_eq)
story.append(Spacer(1, 0.5*cm))

# ── 7. CONDICIONES COMERCIALES ────────────────────────────────────────────────
story.append(Paragraph("7. Condiciones comerciales", h1))
story.append(Paragraph("Forma de pago:", h3))
story.append(Paragraph("• Proyectos: 40% a la firma del contrato, 30% al entregable PoC, 30% al go-live.", bullet))
story.append(Paragraph("• Mantenimiento y retainer: facturación mensual anticipada.", bullet))
story.append(Paragraph("• Talleres: 100% prepago con 10 días de antelación.", bullet))
story.append(Paragraph("• Bolsa de horas: 100% prepago, caducidad 12 meses.", bullet))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("Descuentos:", h3))
story.append(Paragraph("• Startups y asociaciones sectoriales: 15% sobre tarifa estándar.", bullet))
story.append(Paragraph("• Pago total por adelantado en proyectos >5.000 €: 8% descuento.", bullet))
story.append(Paragraph("• Clientes referidos por cliente activo: 10% en primer proyecto.", bullet))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph("Propiedad intelectual:", h3))
story.append(Paragraph(
    "El cliente adquiere la propiedad total del código desarrollado a medida al finalizar el pago. "
    "Los modelos base de terceros (OpenAI, Anthropic) se rigen por sus respectivas licencias. "
    "IAlex Solutions se reserva el derecho de mencionar el proyecto como referencia salvo acuerdo de confidencialidad.", body))

# ── 8. POLÍTICA DE CONFIDENCIALIDAD ───────────────────────────────────────────
story.append(Paragraph("8. Política de confidencialidad y RGPD", h1))
story.append(Paragraph(
    "IAlex Solutions trata los datos de sus clientes conforme al Reglamento General de Protección "
    "de Datos (RGPD / UE 2016/679) y la LOPDGDD. Todos los datos compartidos durante el proyecto "
    "se tratan bajo acuerdo de confidencialidad (NDA) y no se ceden a terceros. "
    "Disponemos de DPA (Data Processing Agreement) estándar que se firma con cada cliente. "
    "Los datos de producción del cliente nunca se usan para entrenar modelos propios. "
    "Para ejercer derechos ARCO: privacidad@ialex-solutions.com.", body))

# ── PIE ────────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 1*cm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    "IAlex Solutions S.L. · CIF B-87654321 · Gran Vía 42, Madrid · hola@ialex-solutions.com · +34 910 123 456",
    caption))
story.append(Paragraph("Documento confidencial — uso interno del Asistente IA — Versión 1.0 Abril 2026", caption))

doc.build(story)
print(f"PDF generado: {OUTPUT}")
