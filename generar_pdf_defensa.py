"""
Generador de PDF para la defensa académica de Ticketia.
Usa ReportLab para soporte completo de Unicode/UTF-8.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import ListFlowable, ListItem
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "TICKETIA_Analisis_Defensa_Academica.pdf")

# ─────────────────────────────────────────────
# ESTILOS
# ─────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_style(name, parent="Normal", **kwargs):
    return ParagraphStyle(name=name, parent=styles[parent], **kwargs)

ST_TITLE = make_style("ST_TITLE", "Title",
    fontSize=28, textColor=colors.HexColor("#1a1a2e"),
    spaceAfter=8, alignment=TA_CENTER)

ST_SUBTITLE = make_style("ST_SUBTITLE", "Normal",
    fontSize=13, textColor=colors.HexColor("#4a4e69"),
    spaceAfter=20, alignment=TA_CENTER)

ST_H1 = make_style("ST_H1", "Heading1",
    fontSize=18, textColor=colors.HexColor("#0d3b66"),
    spaceBefore=22, spaceAfter=10,
    borderPad=4)

ST_H2 = make_style("ST_H2", "Heading2",
    fontSize=13, textColor=colors.HexColor("#1a5276"),
    spaceBefore=14, spaceAfter=6)

ST_H3 = make_style("ST_H3", "Heading3",
    fontSize=11, textColor=colors.HexColor("#1f618d"),
    spaceBefore=10, spaceAfter=4)

ST_BODY = make_style("ST_BODY", "Normal",
    fontSize=10, leading=15, textColor=colors.HexColor("#2c2c2c"),
    spaceAfter=6, alignment=TA_JUSTIFY)

ST_CODE = make_style("ST_CODE", "Code",
    fontSize=8.5, leading=13,
    backColor=colors.HexColor("#f4f4f4"),
    textColor=colors.HexColor("#c0392b"),
    leftIndent=10, rightIndent=10,
    spaceAfter=8, spaceBefore=4)

ST_BULLET = make_style("ST_BULLET", "Normal",
    fontSize=10, leading=15,
    leftIndent=18, bulletIndent=6,
    textColor=colors.HexColor("#2c2c2c"),
    spaceAfter=4)

ST_CAPTION = make_style("ST_CAPTION", "Normal",
    fontSize=8, textColor=colors.HexColor("#7f8c8d"),
    alignment=TA_CENTER, spaceAfter=10)

ST_HIGHLIGHT = make_style("ST_HIGHLIGHT", "Normal",
    fontSize=10, leading=15,
    backColor=colors.HexColor("#eaf4fb"),
    borderColor=colors.HexColor("#2e86c1"),
    borderWidth=1, borderPad=8,
    textColor=colors.HexColor("#1a5276"),
    spaceAfter=8, spaceBefore=4)

ST_WARNING = make_style("ST_WARNING", "Normal",
    fontSize=10, leading=15,
    backColor=colors.HexColor("#fef9e7"),
    textColor=colors.HexColor("#7d6608"),
    leftIndent=10, spaceAfter=6, spaceBefore=4)

ST_TOC = make_style("ST_TOC", "Normal",
    fontSize=10, leading=18, textColor=colors.HexColor("#2c2c2c"),
    leftIndent=10)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def h1(text): return Paragraph(text, ST_H1)
def h2(text): return Paragraph(text, ST_H2)
def h3(text): return Paragraph(text, ST_H3)
def body(text): return Paragraph(text, ST_BODY)
def code(text): return Paragraph(text.replace(" ", "&nbsp;").replace("\n", "<br/>"), ST_CODE)
def space(n=0.3): return Spacer(1, n * cm)
def hr(): return HRFlowable(width="100%", thickness=1, color=colors.HexColor("#bdc3c7"), spaceAfter=8)
def bullet(text): return Paragraph(f"&#8226;&nbsp;&nbsp;{text}", ST_BULLET)
def highlight(text): return Paragraph(text, ST_HIGHLIGHT)
def warning(text): return Paragraph(f"<b>Atencion:</b> {text}", ST_WARNING)

def section_divider(title):
    return [
        space(0.5),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0d3b66")),
        Paragraph(title, ST_H1),
        space(0.2),
    ]

def table(data, col_widths, header=True):
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0 if header else -1),
         colors.HexColor("#0d3b66") if header else colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdc3c7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(style))
    return t

# ─────────────────────────────────────────────
# CONTENIDO
# ─────────────────────────────────────────────
def build_content():
    story = []
    W = 16.5 * cm  # ancho util

    # ── PORTADA ──────────────────────────────────────────────────────────────
    story += [
        space(3),
        Paragraph("TICKETIA", ST_TITLE),
        Paragraph("Plataforma de IA para la Gestion Empresarial Automatizada", ST_SUBTITLE),
        space(0.5),
        HRFlowable(width="80%", thickness=3, color=colors.HexColor("#0d3b66")),
        space(0.5),
        Paragraph("Analisis Tecnico Completo para Defensa Academica", make_style(
            "PORT2", "Normal", fontSize=15, textColor=colors.HexColor("#4a4e69"),
            alignment=TA_CENTER, spaceAfter=6)),
        space(0.3),
        Paragraph("Trabajo Fin de Master — Ingenieria de Sistemas IA", make_style(
            "PORT3", "Normal", fontSize=11, textColor=colors.HexColor("#7f8c8d"),
            alignment=TA_CENTER)),
        space(0.5),
        Paragraph("Alejandro Brata &nbsp;|&nbsp; 2026", make_style(
            "PORT4", "Normal", fontSize=10, textColor=colors.HexColor("#95a5a6"),
            alignment=TA_CENTER)),
        PageBreak(),
    ]

    # ── INDICE ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Indice de Contenidos", ST_H1))
    story.append(hr())
    toc_items = [
        ("1.", "Mapa Completo del Proyecto — Estructura de Carpetas y Archivos", "3"),
        ("2.", "Modulos Principales y sus Responsabilidades", "6"),
        ("3.", "Sistema de Agentes — Tipos, Funciones y Comunicacion", "9"),
        ("3.1.", "Agentes Reactivos", "10"),
        ("3.2.", "Agentes Especializados invocados por el Manager", "11"),
        ("3.3.", "Agentes Proactivos y Scheduler", "12"),
        ("3.4.", "Consejo Estrategico Multi-Persona", "13"),
        ("3.5.", "Flujo de Comunicacion Global", "14"),
        ("4.", "Librerias del requirements.txt — Rol en el Proyecto", "15"),
        ("5.", "Puntos Criticos para el Tribunal", "19"),
        ("5.1.", "Decisiones de Arquitectura y su Justificacion", "19"),
        ("5.2.", "Debilidades Conocidas y Respuestas Preparadas", "22"),
        ("5.3.", "Preguntas Frecuentes de Tribunal — Respuestas Modelo", "24"),
    ]
    for num, title, page in toc_items:
        story.append(Paragraph(
            f"<b>{num}</b>&nbsp;&nbsp;&nbsp;{title}"
            f"<font color='#95a5a6'>&nbsp;&nbsp;........&nbsp;&nbsp;{page}</font>",
            ST_TOC))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECCION 1 — ESTRUCTURA
    # ══════════════════════════════════════════════════════════════════════════
    story += section_divider("1. Mapa Completo del Proyecto — Estructura de Carpetas y Archivos")

    story.append(body(
        "Ticketia es una plataforma SaaS multi-tenant de asistencia empresarial basada en Inteligencia Artificial. "
        "El codigo fuente reside en la carpeta <b>TICKETIA_PRO/</b> dentro del repositorio, con una organizacion "
        "modular clara que separa responsabilidades por dominios funcionales: rutas web, logica de negocio, "
        "agentes IA, servicios externos y configuracion del nucleo."
    ))

    story.append(h2("1.1. Estructura raiz del repositorio"))
    story.append(body(
        "El repositorio contiene, ademas del codigo fuente principal, ficheros de infraestructura "
        "para despliegue (Docker, docker-compose), documentacion academica y scripts auxiliares:"
    ))
    root_tree = [
        ("Fichero / Carpeta", "Descripcion"),
        ("TICKETIA_PRO/", "Directorio principal — toda la logica de la aplicacion"),
        ("Dockerfile", "Imagen Docker para despliegue en contenedor"),
        ("docker-compose.yml", "Orquestacion de servicios: app + base de datos"),
        ("requirements.txt", "Dependencias Python del proyecto"),
        ("ARCHITECTURE_DEFENSE.md", "Documento de arquitectura para la defensa"),
        ("PROPUESTA_TFM_TICKETIA.md", "Propuesta original del Trabajo Fin de Master"),
        ("zip_delivery.py", "Script para empaquetar la entrega academica"),
        (".dockerignore", "Exclusiones del contexto Docker"),
        ("test_docker/", "Tests de validacion del contenedor"),
    ]
    story.append(table(root_tree, [4*cm, 12*cm]))
    story.append(space())

    story.append(h2("1.2. Estructura interna de TICKETIA_PRO/"))
    story.append(body(
        "La aplicacion sigue una arquitectura en capas con separacion clara entre "
        "presentacion (routes, templates), logica de negocio (modules) y configuracion (core):"
    ))

    struct_data = [
        ("Ruta", "Tipo", "Descripcion"),
        ("app.py", ".py", "Entry point: inicializa Flask, BD, admin panel, blueprints"),
        ("mcp_server.py", ".py", "Servidor MCP — expone herramientas al LLM via protocolo MCP/stdio"),
        ("mcp_server_sse.py", ".py", "Variante SSE del servidor MCP para conexiones de larga duracion"),
        ("core/config.py", ".py", "Gestion de variables de entorno y configuracion global"),
        ("core/db_models.py", ".py", "Modelos SQLAlchemy — toda la estructura de la base de datos"),
        ("core/clients.py", ".py", "Clientes singleton: OpenAI, Twilio (evitan reconexiones)"),
        ("core/mcp_client.py", ".py", "Cliente async que lanza mcp_server como subprocess y ejecuta tools"),
        ("core/notifier.py", ".py", "Sistema de notificaciones internas en la plataforma web"),
        ("core/storage.py", ".py", "Gestion de ficheros subidos (tickets, imagenes, audios)"),
        ("modules/agents/manager.py", ".py", "Motor principal: recibe mensaje, llama GPT-4o, ejecuta tools"),
        ("modules/agents/tools.py", ".py", "Definicion JSON de herramientas para el LLM (function calling)"),
        ("modules/agents/history.py", ".py", "Memoria conversacional — recupera ultimas N interacciones"),
        ("modules/agents/background_tasks.py", ".py", "Procesamiento async en hilos secundarios (marketing)"),
        ("modules/chatbot/logic.py", ".py", "Chatbot simple de fallback sin herramientas"),
        ("modules/council/orchestrator.py", ".py", "Debate multi-persona: 3 roles IA en 3 rondas + sintesis"),
        ("modules/proactive/scheduler.py", ".py", "Planificador de agentes proactivos con libreria schedule"),
        ("modules/proactive/admin_redactor.py", ".py", "Agente: clasificacion de imagenes y redaccion de docs"),
        ("modules/proactive/business_health.py", ".py", "Agente: analisis de salud financiera del negocio"),
        ("modules/proactive/grant_hunter.py", ".py", "Agente: busqueda de subvenciones en BOE y web"),
        ("modules/proactive/marketing_agent.py", ".py", "Agente: generacion de contenido de marketing (img/ppt/video)"),
        ("modules/proactive/networker.py", ".py", "Agente: deteccion de sinergias entre usuarios"),
        ("modules/proactive/post_sales.py", ".py", "Agente: gestion de postventa y atencion al cliente"),
        ("modules/services/document.py", ".py", "Generacion de PDFs con fpdf y presentaciones con python-pptx"),
        ("modules/services/notification.py", ".py", "Envio de emails (Flask-Mail) y mensajes WhatsApp (Twilio)"),
        ("modules/services/whatsapp_dispatcher.py", ".py", "Dispatcher: clasifica y enruta mensajes WhatsApp entrantes"),
        ("modules/tickets/logic.py", ".py", "OCR y procesamiento de tickets/facturas via vision GPT-4o"),
        ("modules/utils/transcriber.py", ".py", "Transcripcion de audio con Whisper API de OpenAI"),
        ("routes/api.py", ".py", "Endpoints REST: chat, upload ticket, upload audio, council stream"),
        ("routes/web.py", ".py", "Rutas HTML: autenticacion, dashboard, documentos, wizard"),
        ("routes/webhooks.py", ".py", "Webhook Twilio: recepcion de mensajes WhatsApp"),
        ("llmops/eval_agents.py", ".py", "Evaluacion de calidad de respuestas con DeepEval (LLMOps)"),
        ("tests/test_proactive_agents.py", ".py", "Tests de agentes proactivos con pytest"),
        ("instance/zeptai.db", ".db", "Base de datos SQLite para desarrollo local"),
    ]
    story.append(table(struct_data, [6.5*cm, 1.5*cm, 8.5*cm]))
    story.append(space())

    story.append(h2("1.3. Carpeta templates/ — Vistas HTML"))
    story.append(body(
        "Las plantillas Jinja2 siguen una estructura jerarquica con herencia: "
        "<b>base.html</b> define el layout global (navbar, sidebar, notificaciones) "
        "y el resto extiende este template base."
    ))
    templates = [
        ("Template", "Descripcion"),
        ("base.html", "Layout maestro: navbar, sidebar, barra de notificaciones"),
        ("landing.html", "Pagina de inicio publica con presentacion del producto"),
        ("login.html / register.html", "Autenticacion: inicio de sesion y registro de nuevos usuarios"),
        ("forgot_password.html", "Formulario de recuperacion de contrasena por email"),
        ("dashboard.html", "Panel principal: metricas, graficas, actividad reciente"),
        ("transactions.html", "Listado de tickets/facturas con filtros y acciones"),
        ("documents.html", "Galeria de documentos generados agrupados por tipo y fecha"),
        ("agents.html", "Marketplace de agentes disponibles con toggle de activacion"),
        ("agent_config.html", "Configuracion individual de cada agente"),
        ("wizard.html", "Onboarding: configuracion inicial del negocio paso a paso"),
        ("demo_panel.html", "Panel de demostracion con datos de ejemplo"),
        ("council.html", "Interfaz del Consejo Estrategico con streaming SSE"),
        ("components/agent_card.html", "Componente reutilizable para tarjetas de agentes"),
    ]
    story.append(table(templates, [5*cm, 11.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECCION 2 — MODULOS PRINCIPALES
    # ══════════════════════════════════════════════════════════════════════════
    story += section_divider("2. Modulos Principales y sus Responsabilidades")

    story.append(body(
        "El proyecto organiza su logica en tres grandes capas: el nucleo (core), "
        "los modulos funcionales (modules) y las rutas (routes). Cada capa tiene "
        "una responsabilidad clara y comunica con las adyacentes a traves de interfaces definidas."
    ))

    story.append(h2("2.1. Capa Core — Configuracion y Persistencia"))

    story.append(h3("app.py — Entry Point y Orquestador de Arranque"))
    story.append(body(
        "Este fichero es el punto de entrada de la aplicacion Flask. Sus responsabilidades son:"
    ))
    for item in [
        "Carga de variables de entorno desde .env mediante python-dotenv",
        "Inicializacion de la base de datos con Flask-SQLAlchemy y creacion de tablas",
        "Registro de Blueprints: web, api y webhooks",
        "Configuracion del panel de administracion con Flask-Admin y vistas protegidas por rol (SecureModelView)",
        "Context processor global que inyecta el conteo de notificaciones no leidas en todas las vistas",
        "Endpoints de notificaciones: GET /api/notifications, POST mark_read, POST mark_all_read",
        "Arranque del servidor en el puerto configurado por variable de entorno PORT (por defecto 5000)",
    ]:
        story.append(bullet(item))
    story.append(space(0.2))

    story.append(h3("core/db_models.py — Modelos de Base de Datos"))
    story.append(body(
        "Define la estructura completa de datos usando SQLAlchemy ORM. Los modelos principales son:"
    ))
    models_data = [
        ("Modelo", "Tabla", "Campos clave", "Relaciones"),
        ("BusinessProfile", "business_profiles",
         "user_phone, business_name, system_prompt, sector, plan_tier",
         "One-to-many con Ticket, Appointment, GeneratedDocument"),
        ("Ticket", "tickets",
         "amount, vendor, category, date, image_path, processed",
         "Many-to-one con BusinessProfile"),
        ("Appointment", "appointments",
         "date, time, client_name, client_phone, owner_phone",
         "Many-to-one con BusinessProfile"),
        ("GeneratedDocument", "generated_documents",
         "doc_type, file_path, created_at, content_summary",
         "Many-to-one con BusinessProfile"),
        ("ChatMessage", "chat_messages",
         "role, content, timestamp, channel",
         "Many-to-one con BusinessProfile"),
        ("AgentConfig", "agent_configs",
         "agent_id, is_active, config_json",
         "Many-to-one con BusinessProfile"),
        ("Notification", "notifications",
         "message, is_read, type, created_at",
         "Many-to-one con BusinessProfile"),
        ("Grant", "grants",
         "title, description, url, deadline, sector",
         "Independiente"),
        ("SynergyMatch", "synergy_matches",
         "user_a, user_b, match_reason, score",
         "Referencia dos BusinessProfiles"),
    ]
    story.append(table(models_data, [3.5*cm, 3.5*cm, 5*cm, 4.5*cm]))
    story.append(space())

    story.append(h3("core/clients.py — Clientes Singleton"))
    story.append(body(
        "Implementa el patron Singleton para los clientes de APIs externas. "
        "El objetivo es evitar reconexiones innecesarias y centralizar la configuracion de credenciales. "
        "Incluye el cliente <b>OpenAI</b> (para GPT-4o y Whisper) y el cliente <b>Twilio</b> "
        "(para WhatsApp). Se inicializan una sola vez al arrancar la aplicacion y se reutilizan "
        "en todos los modulos que los necesitan."
    ))
    story.append(space(0.2))

    story.append(h2("2.2. Capa Routes — Presentacion y API"))

    story.append(h3("routes/web.py — Rutas HTML (784 lineas)"))
    story.append(body(
        "Es el fichero mas extenso de rutas. Implementa el ciclo completo de vida del usuario en la plataforma:"
    ))
    web_routes = [
        ("Ruta", "Metodo", "Descripcion"),
        ("/", "GET", "Landing page publica; redirige al dashboard si hay sesion activa"),
        ("/register", "GET/POST", "Registro con validacion de email unico y formato de telefono"),
        ("/login", "GET/POST", "Autenticacion por email+password con hashing bcrypt"),
        ("/logout", "GET", "Limpia la sesion Flask y redirige al login"),
        ("/forgot_password", "POST", "Genera token de reset y envia email con enlace temporal"),
        ("/reset_password/<token>", "GET/POST", "Valida token y actualiza contrasena"),
        ("/dashboard", "GET", "Metricas del mes: gastos, tickets, chats, actividad reciente"),
        ("/transactions", "GET", "Listado completo de tickets con filtros por fecha/categoria"),
        ("/documents", "GET", "Galeria de documentos agrupados por tipo (propuestas, facturas, marketing)"),
        ("/export_excel", "GET", "Exporta gastos a Excel con formato profesional (XlsxWriter)"),
        ("/marketplace", "GET", "Catalogo de agentes disponibles con estado activo/inactivo"),
        ("/toggle_agent/<id>", "POST", "Activa o desactiva un agente para el usuario"),
        ("/agent_config/<id>", "GET", "Pagina de configuracion detallada del agente"),
        ("/save_agent_config/<id>", "POST", "Guarda configuracion del agente en JSON dentro de la BD"),
        ("/wizard", "GET/POST", "Wizard de onboarding para configurar el perfil de negocio"),
        ("/council", "GET", "Interfaz del Consejo Estrategico"),
        ("/demo/seed_data", "POST", "Inyecta datos historicos de ejemplo para demostraciones"),
        ("/demo/trigger/<agent>", "POST", "Dispara manualmente un agente proactivo especifico"),
    ]
    story.append(table(web_routes, [4.5*cm, 2*cm, 10*cm]))
    story.append(space())

    story.append(h3("routes/api.py — Endpoints REST"))
    api_routes = [
        ("Endpoint", "Descripcion"),
        ("POST /api/chat", "Chat web autenticado; ejecuta AgentExecutor con canal 'web'"),
        ("POST /upload_web_ticket", "Sube imagen de ticket; procesa OCR y extrae datos"),
        ("POST /upload_web_audio", "Sube audio WebM; transcribe con Whisper y ejecuta agente"),
        ("POST /generate_video_from_image", "Genera video con Runway ML desde imagen subida"),
        ("POST /api/council/stream", "Stream SSE del debate del Consejo Estrategico"),
    ]
    story.append(table(api_routes, [5*cm, 11.5*cm]))
    story.append(space())

    story.append(h3("routes/webhooks.py — Integracion Twilio"))
    story.append(body(
        "Recibe las peticiones HTTP de Twilio cuando llega un mensaje a los numeros WhatsApp configurados. "
        "Valida la firma de Twilio (X-Twilio-Signature) para evitar peticiones fraudulentas. "
        "Delega el procesamiento al <b>WhatsAppWebhookDispatcher</b> en modules/services/whatsapp_dispatcher.py."
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECCION 3 — AGENTES
    # ══════════════════════════════════════════════════════════════════════════
    story += section_divider("3. Sistema de Agentes — Tipos, Funciones y Comunicacion")

    story.append(body(
        "Ticketia implementa una arquitectura multi-agente donde diferentes agentes IA especializados "
        "colaboran para dar servicio al usuario. Los agentes se clasifican en tres categorias segun "
        "su patron de activacion: <b>reactivos</b> (responden al usuario en tiempo real), "
        "<b>especializados</b> (invocados por el agente principal como subagentes) y "
        "<b>proactivos</b> (se ejecutan autonomamente en background sin intervencion del usuario)."
    ))
    story.append(highlight(
        "<b>Patron arquitectonico:</b> El sistema sigue un patron de orquestacion con un agente "
        "central (AgentExecutor) que actua como router/orchestrator, delegando en agentes "
        "especializados segun el tipo de tarea detectada por el LLM."
    ))
    story.append(space(0.2))

    story.append(h2("3.1. Agentes Reactivos"))

    story.append(h3("AgentExecutor — modules/agents/manager.py"))
    story.append(body(
        "Es el cerebro del sistema. Se instancia para cada mensaje entrante y gestiona el ciclo "
        "completo de procesamiento. Su flujo de ejecucion es el siguiente:"
    ))
    for i, step in enumerate([
        "Recibe: mensaje de texto, numero de telefono, perfil de negocio, URL de media y canal (whatsapp/web)",
        "Si hay imagen adjunta: dispatch directo a AdminRedactor para clasificacion",
        "Guarda la interaccion del usuario en el historial de chat (tabla chat_messages)",
        "Construye el contexto: system prompt del negocio + ultimas 10 interacciones",
        "Primera llamada a GPT-4o con lista de herramientas disponibles (function calling)",
        "Si el modelo devuelve tool_calls: ejecuta cada herramienta secuencialmente",
        "Anade los resultados de herramientas al historial de mensajes",
        "Segunda llamada a GPT-4o para sintetizar resultados de herramientas en respuesta natural",
        "Guarda la respuesta final en el historial y en el log de actividad",
        "Retorna la respuesta final al canal de origen (WhatsApp o web)",
    ], 1):
        story.append(bullet(f"<b>Paso {i}:</b> {step}"))
    story.append(space(0.2))

    story.append(body("<b>Herramientas disponibles para el LLM (definidas en tools.py):</b>"))
    tools_data = [
        ("Herramienta", "Descripcion", "Agente invocado"),
        ("check_availability", "Consulta disponibilidad de agenda para una fecha/hora", "Directo en BD"),
        ("book_appointment", "Crea una cita en la base de datos", "Directo en BD"),
        ("create_proposal_from_last_image", "Genera PDF de propuesta desde la ultima imagen recibida", "AdminRedactor"),
        ("create_proposal_from_text", "Genera PDF desde datos estructurados en texto", "AdminRedactor"),
        ("generate_marketing_material", "Lanza generacion async de contenido de marketing", "MarketingAgent (background)"),
        ("handle_customer_service", "Deriva al agente de postventa", "PostSalesAgent"),
    ]
    story.append(table(tools_data, [4.5*cm, 7*cm, 5*cm]))
    story.append(space())

    story.append(h3("Chatbot Simple — modules/chatbot/logic.py"))
    story.append(body(
        "Agente de fallback que se usa cuando no existe un perfil de negocio configurado. "
        "No tiene acceso a herramientas. Simplemente llama al LLM con un system prompt generico "
        "e implementa un guardrail para mantener las respuestas en el dominio empresarial. "
        "Su funcion principal es orientar a nuevos usuarios hacia el proceso de registro y configuracion."
    ))
    story.append(space(0.2))

    story.append(h2("3.2. Agentes Especializados (Subagentes)"))

    story.append(h3("AdminRedactor — modules/proactive/admin_redactor.py"))
    story.append(body(
        "Agente dual con dos capacidades principales:"
    ))
    story.append(bullet("<b>Clasificador de imagenes:</b> Cuando recibe una imagen, "
        "usa vision de GPT-4o para determinar si es un borrador/esquema de propuesta "
        "o un ticket/factura comercial. Esta clasificacion determina el flujo posterior."))
    story.append(bullet("<b>Redactor de documentos:</b> Genera propuestas y presupuestos "
        "profesionales en PDF. Puede trabajar desde una imagen (extrae la informacion visualmente) "
        "o desde datos estructurados en texto. El PDF se genera con fpdf y se envia por email."))
    story.append(space(0.2))

    story.append(h3("MarketingAgent — modules/proactive/marketing_agent.py"))
    story.append(body(
        "Agente de generacion de contenido de marketing. Siempre se ejecuta en un hilo "
        "secundario (background_tasks.py) para no bloquear la respuesta HTTP. "
        "Puede generar tres tipos de contenido:"
    ))
    story.append(bullet("<b>Imagenes de marketing:</b> Usa DALL-E 3 o la API de OpenAI para generar imagenes profesionales basadas en el prompt del usuario"))
    story.append(bullet("<b>Presentaciones PowerPoint:</b> Genera ficheros .pptx con python-pptx con slides estructuradas, titulos, contenido y estilo de marca"))
    story.append(bullet("<b>Videos:</b> Usa el SDK de Runway ML para generar videos cortos a partir de imagenes de referencia"))
    story.append(body(
        "Una vez generado el contenido, notifica al usuario via WhatsApp (si el canal es WhatsApp) "
        "o crea una notificacion interna en la plataforma web. El fichero se guarda en la BD "
        "como GeneratedDocument."
    ))
    story.append(space(0.2))

    story.append(h3("PostSalesAgent — modules/proactive/post_sales.py"))
    story.append(body(
        "Agente especializado en la gestion de la relacion postventa con clientes. "
        "Se activa cuando el LLM detecta intencion de atencion al cliente en el mensaje. "
        "Sus capacidades incluyen: gestion de quejas y reclamaciones, seguimiento de pedidos, "
        "envio de encuestas de satisfaccion y recordatorios de citas pendientes. "
        "Mantiene el tono y la personalidad configurada en el perfil de negocio del usuario."
    ))
    story.append(space(0.2))

    story.append(h2("3.3. Agentes Proactivos y Scheduler"))

    story.append(body(
        "Los agentes proactivos son la caracteristica diferencial de Ticketia respecto a un chatbot "
        "convencional. Se ejecutan periodicamente en background, analizan la situacion de cada negocio "
        "y generan alertas, recomendaciones o acciones sin que el usuario lo solicite."
    ))

    proactive_data = [
        ("Agente", "Archivo", "Frecuencia", "Funcion Principal", "Output"),
        ("BusinessHealthAgent", "business_health.py", "Diaria",
         "Analiza metricas financieras: gastos del mes, tendencias, anomalias",
         "Alerta WhatsApp si detecta desviacion significativa"),
        ("GrantHunter", "grant_hunter.py", "Semanal",
         "Busca subvenciones en BOE, CDTI y webs de ayudas usando DuckDuckGo",
         "Guarda grants en BD; notifica al usuario de nuevas oportunidades"),
        ("Networker", "networker.py", "Semanal",
         "Compara perfiles de negocio en la plataforma y detecta sinergias potenciales",
         "Crea SynergyMatch en BD; sugiere contacto entre usuarios complementarios"),
        ("MarketingAgent", "marketing_agent.py", "Bajo demanda",
         "Genera contenido de marketing (imagenes, PPT, video) segun briefing",
         "Fichero guardado en BD; notificacion al usuario cuando esta listo"),
    ]
    story.append(table(proactive_data, [3.5*cm, 3.5*cm, 2*cm, 5*cm, 2.5*cm]))
    story.append(space())

    story.append(h3("Scheduler — modules/proactive/scheduler.py"))
    story.append(body(
        "Usa la libreria <b>schedule</b> de Python para planificar la ejecucion periodica de los agentes. "
        "Se ejecuta en un hilo separado al arrancar la aplicacion. Itera sobre todos los "
        "BusinessProfiles activos y ejecuta cada agente con el contexto del negocio correspondiente. "
        "<b>Limitacion conocida:</b> schedule no persiste entre reinicios del servidor; "
        "si la aplicacion se reinicia, el scheduler vuelve a empezar desde cero."
    ))
    story.append(space(0.2))

    story.append(h2("3.4. Consejo Estrategico Multi-Persona"))

    story.append(h3("CouncilManager — modules/council/orchestrator.py"))
    story.append(body(
        "El Consejo Estrategico es la caracteristica mas innovadora del sistema desde el punto de "
        "vista de diseno de agentes. Implementa un debate estructurado entre tres personas IA "
        "con perspectivas distintas sobre el mismo LLM (GPT-4o), cada una con un system prompt "
        "diferente que define su rol, personalidad y area de conocimiento."
    ))

    personas_data = [
        ("Persona", "Icono", "Perfil", "Area", "Estilo de Comunicacion"),
        ("El Socio", "Tigre", "Emprendedor agresivo orientado al crecimiento",
         "Ventas, expansion, captacion de clientes", "Frases cortas, directo, ambicioso"),
        ("El Gestor", "Buho", "Experto legal y fiscal conservador",
         "Cumplimiento, riesgos, obligaciones tributarias", "Prudente, detallista, preventivo"),
        ("El Coach", "Cohete", "Consultor de productividad y personas",
         "Procesos, equipo, bienestar empresarial", "Empatico, practico, motivador"),
    ]
    story.append(table(personas_data, [2.5*cm, 1.5*cm, 4*cm, 3.5*cm, 5*cm]))
    story.append(space())

    story.append(body("<b>Protocolo de debate — 3 rondas:</b>"))
    for ronda, desc in [
        ("Ronda 1 — Posiciones iniciales",
         "Cada persona da su opinion inicial sobre el tema propuesto. "
         "Se ejecutan secuencialmente para crear la sensacion de una conversacion natural."),
        ("Ronda 2 — Replicas",
         "Cada persona reacciona a las opiniones de las otras dos (maximo 25 palabras por replica). "
         "Esta limitacion fuerza argumentos concisos y centrados."),
        ("Ronda 3 — Sintesis y plan de accion",
         "Se genera un plan de accion en formato Markdown que integra las tres perspectivas, "
         "identificando puntos de consenso y acciones concretas ordenadas por prioridad."),
    ]:
        story.append(bullet(f"<b>{ronda}:</b> {desc}"))
    story.append(space(0.2))

    story.append(body(
        "<b>Implementacion tecnica:</b> Usa <b>AsyncOpenAI</b> para las llamadas al LLM "
        "y un generador de eventos para el streaming via SSE (Server-Sent Events). "
        "El frontend consume el stream con EventSource de JavaScript y va mostrando "
        "las intervenciones de cada persona en tiempo real. Opcionalmente, cada persona "
        "puede usar herramientas MCP durante sus intervenciones para consultar datos reales "
        "(e.g., El Gestor puede buscar normativa fiscal vigente con search_web)."
    ))
    story.append(space(0.2))

    story.append(h2("3.5. Flujo de Comunicacion Global"))

    story.append(body(
        "El siguiente diagrama describe el flujo completo desde que un mensaje entra "
        "al sistema hasta que se genera la respuesta:"
    ))

    flow_text = (
        "ENTRADA WhatsApp\n"
        "  └─> webhooks.py (valida firma Twilio)\n"
        "        └─> WhatsAppDispatcher\n"
        "              ├─ ¿Numero dedicado del cliente?\n"
        "              │     └─> AgentExecutor (negocio especifico)\n"
        "              └─ ¿Numero central de Ticketia?\n"
        "                    ├─ ¿Audio? ──> Whisper (transcripcion) ──> AgentExecutor\n"
        "                    ├─ ¿Imagen? ─> AdminRedactor (clasificar)\n"
        "                    │               ├─ Borrador ──> AgentExecutor (con media_url)\n"
        "                    │               └─ Ticket ───> tickets/logic.py (OCR)\n"
        "                    └─ ¿Texto? ──> AgentExecutor\n"
        "\n"
        "DENTRO de AgentExecutor:\n"
        "  └─> GPT-4o (con tools + historial + system prompt)\n"
        "        ├─ tool: book_appointment    ──> BD directa\n"
        "        ├─ tool: create_proposal     ──> AdminRedactor ──> PDF ──> Email\n"
        "        ├─ tool: generate_marketing  ──> background_tasks ──> MarketingAgent\n"
        "        ├─ tool: handle_cs           ──> PostSalesAgent\n"
        "        └─ tool: [MCP tools]         ──> mcp_client ──> mcp_server\n"
        "                                           ├─ get_financial_summary (BD)\n"
        "                                           ├─ search_web (DuckDuckGo)\n"
        "                                           ├─ schedule_appointment (BD)\n"
        "                                           └─ send_email_notification (SMTP)\n"
        "\n"
        "ENTRADA Web (chat en dashboard)\n"
        "  └─> routes/api.py POST /api/chat\n"
        "        └─> AgentExecutor (canal='web')\n"
        "              [mismo flujo que arriba]\n"
        "\n"
        "COUNCIL (streaming):\n"
        "  └─> routes/api.py POST /api/council/stream\n"
        "        └─> CouncilManager.run_session()\n"
        "              ├─ Ronda 1: El Socio, El Gestor, El Coach (opiniones)\n"
        "              ├─ Ronda 2: replicas cruzadas\n"
        "              └─ Ronda 3: sintesis ──> SSE stream ──> frontend\n"
        "\n"
        "PROACTIVO (background, sin usuario):\n"
        "  └─> scheduler.py (hilo separado)\n"
        "        ├─ BusinessHealthAgent ──> analisis + notificacion\n"
        "        ├─ GrantHunter ──> busqueda web + guardado en BD\n"
        "        └─ Networker ──> comparacion perfiles + SynergyMatch"
    )
    story.append(Paragraph(flow_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), ST_CODE))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECCION 4 — LIBRERIAS
    # ══════════════════════════════════════════════════════════════════════════
    story += section_divider("4. Librerias del requirements.txt — Rol en el Proyecto")

    story.append(body(
        "A continuacion se detalla cada dependencia del proyecto con su uso concreto, "
        "el modulo que la consume y la justificacion de su eleccion frente a alternativas."
    ))

    story.append(h2("4.1. Framework Web y Base de Datos"))

    libs_web = [
        ("Libreria", "Version", "Modulo que la usa", "Uso concreto en Ticketia", "Alternativas consideradas"),
        ("flask", ">=2.x", "app.py, routes/*",
         "Framework web principal: routing, sesiones, blueprints, contexto de aplicacion, templates Jinja2",
         "FastAPI (mas moderno pero innecesariamente complejo para un MVP sync), Django (demasiado opinionado)"),
        ("flask-sqlalchemy", ">=3.x", "core/db_models.py, todos los modulos",
         "ORM que mapea clases Python a tablas SQL; gestiona sesiones de BD, migraciones y relaciones entre modelos",
         "SQLAlchemy puro (mas verboso), Peewee (menos maduro)"),
        ("flask-mail", ">=0.9", "modules/services/notification.py, app.py",
         "Envio de emails transaccionales: documentos PDF adjuntos, reset de contrasena, notificaciones de agentes",
         "smtplib puro (mas codigo), SendGrid SDK (dependencia externa de pago)"),
        ("flask-admin", ">=1.6", "app.py",
         "Panel de administracion con CRUD automatico de modelos; acceso restringido por rol mediante SecureModelView",
         "Implementacion manual (mucho mas tiempo), Django Admin (requiere migrar a Django)"),
        ("psycopg2-binary", ">=2.9", "core/config.py (DB URL)",
         "Driver de conexion PostgreSQL para entorno de produccion; SQLite se usa en desarrollo",
         "asyncpg (solo async), pg8000 (puro Python, mas lento)"),
    ]
    story.append(table(libs_web, [2.5*cm, 1.5*cm, 3.5*cm, 5*cm, 4*cm]))
    story.append(space())

    story.append(h2("4.2. Inteligencia Artificial y LLM"))

    libs_ai = [
        ("Libreria", "Modulo que la usa", "Uso concreto en Ticketia"),
        ("openai", "manager.py, council/orchestrator.py, tickets/logic.py, utils/transcriber.py",
         "GPT-4o para razonamiento y generacion de texto; GPT-4o Vision para OCR de tickets e imagenes; "
         "DALL-E 3 para generacion de imagenes de marketing; Whisper API para transcripcion de audios "
         "enviados por WhatsApp. Es la dependencia mas critica del sistema."),
        ("mcp[cli]", "mcp_server.py, mcp_server_sse.py, core/mcp_client.py",
         "Implementacion del Model Context Protocol de Anthropic. Se usa FastMCP para definir el servidor "
         "de herramientas y el cliente async para consumirlo. Permite que el LLM decida en runtime "
         "que herramienta usar sin logica condicional en el codigo."),
        ("duckduckgo-search", "mcp_server.py, proactive/grant_hunter.py",
         "Motor de busqueda web privado y gratuito. Se usa en la herramienta search_web del MCP "
         "y en el GrantHunter para buscar subvenciones en BOE, CDTI y otros portales publicos."),
        ("deepeval", "llmops/eval_agents.py",
         "Framework de evaluacion de calidad de respuestas LLM. Mide metricas como Answer Relevancy, "
         "Faithfulness y Contextual Precision para evaluar si los agentes responden correctamente. "
         "Parte del pipeline de LLMOps del proyecto."),
        ("runwayml", "proactive/marketing_agent.py",
         "SDK oficial de Runway ML para generacion de videos con IA. Se usa para crear videos cortos "
         "a partir de imagenes de referencia cuando el usuario solicita contenido de video marketing."),
    ]
    story.append(table(libs_ai, [2.5*cm, 4.5*cm, 9.5*cm]))
    story.append(space())

    story.append(h2("4.3. Integraciones Externas"))

    libs_ext = [
        ("Libreria", "Modulo que la usa", "Uso concreto en Ticketia"),
        ("twilio", "routes/webhooks.py, modules/services/notification.py",
         "Integracion con la API de WhatsApp Business via Twilio. Recibe webhooks de mensajes entrantes, "
         "envia respuestas de texto, comparte archivos multimedia (PDFs, imagenes, videos). "
         "Tambien valida la firma de las peticiones para seguridad."),
        ("requests", "proactive/grant_hunter.py, proactive/marketing_agent.py",
         "Llamadas HTTP a APIs externas: descarga de archivos multimedia de Twilio, "
         "llamadas a la API de Runway ML, scraping de portales de subvenciones."),
        ("python-dotenv", "core/config.py",
         "Carga de variables de entorno desde el fichero .env: API keys de OpenAI y Twilio, "
         "credenciales de base de datos, configuracion de email SMTP, clave secreta de Flask."),
    ]
    story.append(table(libs_ext, [2.5*cm, 4.5*cm, 9.5*cm]))
    story.append(space())

    story.append(h2("4.4. Generacion de Documentos"))

    libs_docs = [
        ("Libreria", "Modulo que la usa", "Uso concreto en Ticketia"),
        ("fpdf", "modules/services/document.py, proactive/admin_redactor.py",
         "Generacion de PDFs programaticos: propuestas comerciales, presupuestos, facturas proforma. "
         "Permite control total del layout, tipografia, colores y logotipo del negocio."),
        ("python-pptx", "proactive/marketing_agent.py",
         "Generacion de presentaciones PowerPoint con diapositivas estructuradas. El MarketingAgent "
         "crea presentaciones con titulo, agenda, contenido de cada slide y slide de cierre, "
         "aplicando los colores corporativos del negocio."),
        ("Pillow", "proactive/marketing_agent.py, proactive/admin_redactor.py",
         "Procesamiento de imagenes: redimensionado antes de enviar a la API de vision, "
         "conversion de formato, insercion de logotipo en documentos generados, "
         "optimizacion de tamano para envio por WhatsApp."),
        ("matplotlib", "proactive/business_health.py",
         "Generacion de graficas de metricas financieras (gastos por categoria, tendencia mensual) "
         "que se incluyen en los informes de salud empresarial generados por el BusinessHealthAgent."),
        ("xlsxwriter", "routes/web.py (/export_excel)",
         "Generacion de ficheros Excel con formato profesional: colores alternados por fila, "
         "formato de moneda, hipervinculos a imagenes de tickets, hoja de resumen con totales."),
    ]
    story.append(table(libs_docs, [2.5*cm, 4.5*cm, 9.5*cm]))
    story.append(space())

    story.append(h2("4.5. Utilidades y Procesamiento de Datos"))

    libs_utils = [
        ("Libreria", "Modulo que la usa", "Uso concreto en Ticketia"),
        ("pandas", "routes/web.py, proactive/business_health.py",
         "Manipulacion de datos tabulares para calculo de metricas: agrupacion de gastos por categoria, "
         "calculo de medias moviles para deteccion de anomalias, preparacion de datos para exportacion Excel."),
        ("python-dateutil", "modules/tickets/logic.py, routes/web.py",
         "Parsing flexible de fechas extraidas de tickets por OCR. Las facturas vienen con formatos "
         "muy variados (DD/MM/YYYY, YYYY-MM-DD, 12 de marzo de 2025, etc.) y dateutil los interpreta todos."),
        ("schedule", "modules/proactive/scheduler.py",
         "Planificacion de tareas periodicas con sintaxis declarativa (schedule.every().day.do(fn)). "
         "Ejecuta los agentes proactivos en el hilo del scheduler sin necesidad de Celery ni Redis."),
        ("gunicorn", "Despliegue (Dockerfile, docker-compose)",
         "Servidor WSGI de produccion. Reemplaza al servidor de desarrollo de Flask. Gestiona "
         "multiples workers para manejar peticiones concurrentes (webhooks de WhatsApp simultaneos)."),
        ("pytest", "tests/",
         "Framework de testing. Se usa para los tests unitarios de los agentes proactivos "
         "y los tests de integracion del pipeline de procesamiento de tickets."),
    ]
    story.append(table(libs_utils, [2.5*cm, 4.5*cm, 9.5*cm]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECCION 5 — PUNTOS CRITICOS
    # ══════════════════════════════════════════════════════════════════════════
    story += section_divider("5. Puntos Criticos para el Tribunal")

    story.append(body(
        "Esta seccion prepara al autor para responder a las preguntas mas exigentes de un tribunal academico. "
        "Cada decision tecnica importante se analiza desde tres angulos: "
        "que se hizo, por que se eligio esa opcion y cuales son sus limitaciones conocidas."
    ))

    story.append(h2("5.1. Decisiones de Arquitectura y su Justificacion"))

    story.append(h3("Decision 1: Flask sobre FastAPI"))
    story.append(body(
        "<b>Que se hizo:</b> Se eligio Flask como framework web principal en lugar de FastAPI."
    ))
    story.append(body(
        "<b>Por que:</b> El 95% de los endpoints del proyecto son sincronos (request/response clasico). "
        "Flask tiene un ecosistema mas maduro para las integraciones necesarias: "
        "Flask-SQLAlchemy, Flask-Mail y Flask-Admin estan extremadamente bien integrados "
        "y permiten construir el panel de administracion, las vistas web y la gestion de BD "
        "con mucho menos codigo. FastAPI anade complejidad async que solo seria beneficiosa "
        "si todos los endpoints fueran async, lo que requeriria un ORM async (SQLAlchemy async) "
        "y complicaria el codigo sin beneficio proporcional en un MVP."
    ))
    story.append(warning(
        "El Consejo Estrategico usa asyncio dentro de una app Flask sincrona, "
        "lo que requiere asyncio.run() o un loop de eventos separado. "
        "Esto es una inconsistencia arquitectonica menor que en una version production-ready "
        "se resolveria migrando el council a un servicio independiente con FastAPI."
    ))
    story.append(space(0.2))

    story.append(h3("Decision 2: Model Context Protocol (MCP)"))
    story.append(body(
        "<b>Que se hizo:</b> Se implemento un servidor MCP (mcp_server.py) usando FastMCP, "
        "y un cliente async (mcp_client.py) que lo consume via subprocess con protocolo stdio."
    ))
    story.append(body(
        "<b>Por que:</b> MCP es el estandar emergente definido por Anthropic para que los LLMs "
        "accedan a herramientas y contexto externo de forma estandarizada. Su adopcion en el proyecto "
        "tiene valor academico y tecnico: desacopla la definicion de herramientas del codigo del agente, "
        "permite que el LLM descubra herramientas en runtime (lista de tools dinamica), "
        "y prepara la arquitectura para integracion con cualquier cliente MCP en el futuro "
        "(Claude Desktop, otros modelos que soporten MCP)."
    ))
    story.append(body(
        "<b>Herramientas expuestas via MCP:</b>"
    ))
    for t in [
        "get_financial_summary(user_phone): consulta la BD y devuelve resumen de gastos del usuario",
        "search_web(query, max_results): busca informacion actual con DuckDuckGo (subvenciones, noticias)",
        "schedule_appointment(owner, date, time, client): crea citas comprobando conflictos en BD",
        "send_email_notification(to, subject, body): envia emails via SMTP/Flask-Mail",
    ]:
        story.append(bullet(t))
    story.append(warning(
        "El servidor MCP se lanza como subprocess con stdio, lo que anade latencia de arranque "
        "(fork de proceso) y complejidad de gestion. Para entornos de alta concurrencia, "
        "la variante SSE (mcp_server_sse.py) es mas apropiada al mantener conexiones persistentes."
    ))
    story.append(space(0.2))

    story.append(h3("Decision 3: Council — Role Prompting vs. Multi-Agente Real"))
    story.append(body(
        "<b>Que se hizo:</b> El Consejo Estrategico implementa tres 'personas' sobre el mismo modelo GPT-4o, "
        "cada una con un system prompt diferente que define su rol, personalidad y area de expertise."
    ))
    story.append(body(
        "<b>Por que:</b> El diseno de personas (role prompting) sobre un unico LLM es un patron bien "
        "documentado en la literatura de sistemas multi-agente basados en LLMs. Ofrece varias ventajas: "
        "consistencia del modelo base (el mismo GPT-4o para todas las perspectivas), "
        "menor costo (un proveedor, una API), "
        "menor latencia (sin overhead de comunicacion entre modelos distintos), "
        "y suficiente diversidad cognitiva para los propositos del sistema (asesoramiento empresarial)."
    ))
    story.append(highlight(
        "<b>Pregunta critica esperada:</b> 'No es esto un unico agente con diferentes prompts? "
        "Como es multi-agente?' <b>Respuesta:</b> Correcto, es un unico modelo con role prompting, "
        "lo que en la literatura se denomina 'persona-based multi-agent simulation'. "
        "La distincion es honesta: no hay modelos separados ni comunicacion real entre agentes. "
        "El valor esta en el protocolo de debate (3 rondas estructuradas) y la sintesis integrada, "
        "no en la heterogeneidad de modelos. Para una version v2 se podrian usar modelos especializados "
        "(GPT-4o para El Socio, Claude para El Gestor, Gemini para El Coach)."
    ))
    story.append(space(0.2))

    story.append(h3("Decision 4: WhatsApp como canal principal"))
    story.append(body(
        "<b>Que se hizo:</b> Se eligio WhatsApp via Twilio como canal de comunicacion principal "
        "en lugar de desarrollar una app movil nativa o una interfaz web-first."
    ))
    story.append(body(
        "<b>Por que:</b> El publico objetivo son autonomos y PYMEs espanolas. "
        "Segun datos de Statista (2024), el 93% de los espanoles usa WhatsApp diariamente. "
        "La adopcion es cero: no hay que instalar nada ni cambiar habitos. "
        "El usuario puede enviar un ticket fotografiandolo directamente desde WhatsApp, "
        "recibir sus documentos por el mismo canal y interactuar con el asistente "
        "con el mismo flujo que usa para hablar con clientes o proveedores."
    ))
    story.append(body(
        "<b>Consideracion tecnica:</b> Twilio actua como capa de abstraccion sobre la API de "
        "WhatsApp Business. Gestiona el numero de telefono, la validacion de mensajes "
        "(firma HMAC en cabecera X-Twilio-Signature) y el envio de archivos multimedia. "
        "La alternativa directa (API oficial de WhatsApp Business de Meta) requiere proceso "
        "de verificacion empresarial que no es viable para un MVP academico."
    ))
    story.append(space(0.2))

    story.append(h3("Decision 5: Multi-tenancy en base de datos compartida"))
    story.append(body(
        "<b>Que se hizo:</b> Todos los negocios (BusinessProfiles) comparten la misma base de datos "
        "PostgreSQL. El aislamiento se implementa a nivel de aplicacion filtrando por user_phone "
        "en todas las consultas."
    ))
    story.append(body(
        "<b>Por que:</b> Es el patron multi-tenant mas simple (shared schema, shared database). "
        "Simplifica enormemente el deployment (una sola instancia de PostgreSQL), "
        "las migraciones de esquema (se aplican a todos los tenants a la vez) y el mantenimiento. "
        "Para un MVP con un numero limitado de usuarios, el rendimiento es suficiente."
    ))
    story.append(warning(
        "El modelo actual no tiene Row Level Security (RLS) en la base de datos. "
        "El aislamiento depende exclusivamente del codigo de aplicacion. "
        "Un bug en el filtrado podria exponer datos de un negocio a otro. "
        "En produccion real se implementaria RLS en PostgreSQL o un esquema por tenant."
    ))
    story.append(space(0.2))

    story.append(h3("Decision 6: GPT-4o sobre modelos open-source"))
    story.append(body(
        "<b>Que se hizo:</b> Se usa exclusivamente GPT-4o de OpenAI como modelo de lenguaje."
    ))
    story.append(body(
        "<b>Por que:</b> Las tareas mas criticas del sistema requieren alta precision en espanol: "
        "OCR de tickets y facturas (con formatos variados, escritura manual, sellos), "
        "extraccion estructurada de datos (importe, proveedor, fecha, categoria fiscal), "
        "y generacion de documentos legales/comerciales. Los benchmarks propios y de la literatura "
        "muestran que GPT-4o supera a los modelos open-source disponibles en 2024-2025 "
        "en estas tareas especificas en espanol."
    ))
    story.append(body(
        "<b>Riesgos conocidos:</b> Dependencia de un proveedor unico (vendor lock-in), "
        "costo variable en funcion del numero de tokens, latencia de red hacia servidores de OpenAI, "
        "y cambios de precio o disponibilidad fuera del control del proyecto."
    ))
    story.append(PageBreak())

    story.append(h2("5.2. Debilidades Conocidas y Respuestas Preparadas"))

    debilidades = [
        (
            "Autenticacion basica (sesiones Flask sin JWT)",
            "El sistema usa sesiones del lado del servidor con Flask-Session. "
            "No hay JWT, no hay OAuth2, no hay 2FA.",
            "Es suficiente para un MVP con usuarios registrados. "
            "En produccion se implementaria OAuth2 (Google/Microsoft) para el segmento empresarial "
            "y JWT para los endpoints de la API REST. "
            "La contrasena se almacena con hashing bcrypt, lo que es correcto.",
        ),
        (
            "Scheduler sin persistencia entre reinicios",
            "La libreria schedule ejecuta tareas en memoria. Si el servidor se reinicia, "
            "las tareas pendientes se pierden y el scheduler empieza desde cero.",
            "Limitacion conocida y documentada del MVP. "
            "En produccion se usaria Celery + Redis (broker de tareas persistente) o APScheduler "
            "con backend de base de datos. La decision de usar schedule priorizo la simplicidad "
            "para el prototipo academico.",
        ),
        (
            "Sin rate limiting en la API",
            "Los endpoints de la API REST y el webhook de WhatsApp no tienen limitacion de frecuencia, "
            "lo que los hace vulnerables a abusos.",
            "El webhook de Twilio esta protegido por validacion de firma HMAC, "
            "lo que previene el abuso desde fuentes externas. "
            "Para los endpoints de la API web se usaria Flask-Limiter en produccion. "
            "En el contexto academico del MVP, el riesgo es asumible.",
        ),
        (
            "MCP via subprocess (latencia y complejidad)",
            "El servidor MCP se lanza como un nuevo proceso Python cada vez que el cliente MCP "
            "necesita ejecutar herramientas, anadiendo latencia de fork.",
            "La arquitectura MCP esta disenada para ser modular: el servidor se puede externalizar "
            "a un proceso persistente o usar la variante SSE (mcp_server_sse.py). "
            "El valor de usar MCP es la interoperabilidad estandarizada, no el rendimiento optimo "
            "en el primer prototipo.",
        ),
        (
            "Tests limitados (cobertura parcial)",
            "El proyecto tiene tests de agentes proactivos y tests de sanidad, "
            "pero la cobertura de codigo es baja en modulos criticos como el AgentExecutor.",
            "El sistema incluye evaluacion LLMOps con DeepEval (llmops/eval_agents.py), "
            "que es la forma correcta de evaluar sistemas IA: medir calidad de respuestas, "
            "relevancia contextual y fidelidad. Los tests unitarios clasicos son menos significativos "
            "para sistemas donde el comportamiento depende del LLM.",
        ),
        (
            "API keys en fichero .env",
            "Las credenciales de OpenAI, Twilio y la BD se gestionan via variables de entorno "
            "en un fichero .env que no se sube al repositorio.",
            "Es el estandar de la industria para desarrollo. "
            "En produccion se usaria un secrets manager: AWS Secrets Manager, "
            "HashiCorp Vault o el sistema de secrets de Kubernetes. "
            "El .env esta en .gitignore y nunca se ha subido al repositorio.",
        ),
    ]

    for debilidad, problema, respuesta in debilidades:
        story.append(KeepTogether([
            h3(f"Debilidad: {debilidad}"),
            Paragraph(f"<b>Descripcion del problema:</b> {problema}", ST_BODY),
            Paragraph(f"<b>Respuesta preparada:</b> {respuesta}", ST_HIGHLIGHT),
            space(0.3),
        ]))

    story.append(h2("5.3. Preguntas Frecuentes de Tribunal — Respuestas Modelo"))

    preguntas = [
        (
            "Como garantizas que los datos de un cliente no sean visibles por otro?",
            "El aislamiento multi-tenant se implementa a dos niveles: "
            "(1) Nivel de aplicacion: todas las consultas SQLAlchemy filtran por user_phone, "
            "que actua como identificador de tenant. "
            "(2) Nivel de sesion: el user_phone del usuario autenticado se almacena en la sesion Flask "
            "y se usa para filtrar cada consulta sin posibilidad de que el usuario lo manipule. "
            "La mejora para produccion seria Row Level Security en PostgreSQL.",
        ),
        (
            "Que pasa si OpenAI tiene una interrupcion de servicio?",
            "El sistema queda degradado: los agentes IA no pueden responder. "
            "No hay fallback a otro LLM en la version actual, lo que es un single point of failure. "
            "La mitigacion a corto plazo seria implementar retry con exponential backoff "
            "(ya parcialmente presente en las llamadas a la API). "
            "La mitigacion a largo plazo seria un router de LLMs que cambie a Anthropic Claude "
            "o Gemini si OpenAI no responde en un tiempo maximo.",
        ),
        (
            "Como evaluas la calidad de las respuestas de los agentes?",
            "El proyecto incluye un pipeline LLMOps en llmops/eval_agents.py usando DeepEval. "
            "Se miden tres metricas principales: "
            "Answer Relevancy (la respuesta responde a lo que el usuario pregunto), "
            "Faithfulness (la respuesta no incluye informacion inventada), "
            "y Contextual Precision (se usa el contexto correcto del negocio). "
            "Los tests de evaluacion se pueden ejecutar contra casos de uso reales documentados "
            "en el gold standard del dataset.",
        ),
        (
            "Por que no usaste LangChain o LlamaIndex?",
            "Decision consciente. LangChain anade una capa de abstraccion que complica el debugging "
            "sin aportar valor proporcional cuando el numero de tipos de agente es bajo y controlado. "
            "El AgentExecutor del proyecto hace exactamente lo que se necesita: "
            "history, tool calling, second call. Escribirlo directamente con la API de OpenAI "
            "da control total, menos dependencias y codigo mas mantenible. "
            "MCP ya estandariza la parte de herramientas, que era lo unico valioso de LangChain tools.",
        ),
        (
            "Como escala el sistema si crece el numero de usuarios?",
            "El sistema escala horizontalmente con gunicorn (multiples workers) detras de un "
            "load balancer. La base de datos PostgreSQL soporta alta concurrencia. "
            "Los cuellos de botella conocidos son: (1) el scheduler single-threaded que se "
            "resuelve con Celery, (2) el servidor MCP subprocess que se resuelve con SSE, "
            "y (3) los hilos de background_tasks que se resuelven con un pool de workers (ThreadPoolExecutor). "
            "El Dockerfile incluido facilita el despliegue en Kubernetes o ECS.",
        ),
        (
            "Por que elegiste WhatsApp y no Telegram o un canal propio?",
            "Por adoption rate: WhatsApp tiene el 93% de penetracion en Espana. "
            "El publico objetivo (autonomos y PYMEs) ya usa WhatsApp para comunicarse con clientes, "
            "por lo que la friccion de adopcion es practicamente nula. "
            "Telegram tiene mejor API tecnica pero mucha menor penetracion en el segmento empresarial espanol. "
            "Un canal propio requiere desarrollo movil nativo (iOS + Android) o una PWA, "
            "lo que esta fuera del alcance del MVP academico.",
        ),
        (
            "Que aporta el sistema MCP respecto a simplemente llamar las funciones directamente?",
            "MCP aporta estandarizacion e interoperabilidad. Con MCP: "
            "(1) el LLM descubre las herramientas disponibles en tiempo de ejecucion, "
            "no en tiempo de compilacion; "
            "(2) el servidor de herramientas puede ser reemplazado sin cambiar el agente; "
            "(3) el mismo servidor MCP puede ser consumido por diferentes clientes "
            "(Claude Desktop, otros agentes, la propia app); "
            "(4) sigue el estandar de la industria, haciendo el sistema interoperable "
            "con el ecosistema emergente de MCP servers de terceros.",
        ),
        (
            "Como manejas el contexto largo en conversaciones extensas?",
            "El AgentExecutor recupera las ultimas 10 interacciones del historial (configurable). "
            "Esto limita el contexto enviado al LLM a una ventana deslizante, "
            "evitando el problema de context window overflow y controlando el costo por token. "
            "La limitacion es que el agente 'olvida' conversaciones muy antiguas. "
            "Una mejora seria implementar memoria semantica: vectorizar el historial con embeddings "
            "y recuperar los mensajes mas relevantes (RAG sobre el historial), no solo los mas recientes.",
        ),
    ]

    for pregunta, respuesta in preguntas:
        story.append(KeepTogether([
            h3(f"P: {pregunta}"),
            Paragraph(f"<b>R:</b> {respuesta}", ST_BODY),
            space(0.3),
        ]))

    # ── CIERRE ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(space(2))
    story.append(HRFlowable(width="80%", thickness=3, color=colors.HexColor("#0d3b66")))
    story.append(space(0.5))
    story.append(Paragraph(
        "Documento generado automaticamente para la defensa del TFM.",
        make_style("CLOSE1", "Normal", fontSize=11,
                   textColor=colors.HexColor("#7f8c8d"), alignment=TA_CENTER)))
    story.append(Paragraph(
        "Ticketia — Plataforma de IA para la Gestion Empresarial Automatizada",
        make_style("CLOSE2", "Normal", fontSize=9,
                   textColor=colors.HexColor("#bdc3c7"), alignment=TA_CENTER)))
    story.append(Paragraph(
        "2026 | Trabajo Fin de Master",
        make_style("CLOSE3", "Normal", fontSize=9,
                   textColor=colors.HexColor("#bdc3c7"), alignment=TA_CENTER)))

    return story


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        title="Ticketia — Analisis Tecnico para Defensa Academica",
        author="Alejandro Brata",
        subject="Trabajo Fin de Master — Ingenieria de Sistemas IA",
    )

    story = build_content()
    doc.build(story)
    print(f"PDF generado correctamente en:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
