"""
Genera la documentación técnica del proyecto Ticketia Pro en PDF.
Uso: python generar_documentacion.py
"""
from fpdf import FPDF
import os

class Doc(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, 'Ticketia Pro - Documentación Técnica TFM', align='L')
        self.cell(0, 8, f'Pág. {self.page_no()}', align='R')
        self.ln(2)
        self.set_draw_color(220, 220, 220)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Alejandro Bravot - TFM 2025', align='C')

    def cover(self):
        self.add_page()
        self.set_fill_color(79, 70, 229)  # indigo-600
        self.rect(0, 0, 210, 297, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 36)
        self.set_y(80)
        self.cell(0, 15, 'Ticketia Pro', align='C')
        self.ln(16)
        self.set_font('Helvetica', '', 18)
        self.cell(0, 10, 'Documentacion Tecnica', align='C')
        self.ln(10)
        self.cell(0, 10, 'Trabajo Fin de Master', align='C')
        self.ln(40)
        self.set_font('Helvetica', '', 12)
        self.set_text_color(199, 210, 254)
        self.cell(0, 8, 'Plataforma de IA Empresarial para PYMEs', align='C')
        self.ln(8)
        self.cell(0, 8, 'Flask + PostgreSQL/pgvector + OpenAI + Docker', align='C')
        self.ln(60)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', '', 11)
        self.cell(0, 8, 'Alejandro Bravot  |  2025', align='C')

    def toc_page(self, sections):
        self.add_page()
        self.h1('Indice de Contenidos')
        self.set_font('Helvetica', '', 10)
        self.set_text_color(60, 60, 60)
        for i, (num, title) in enumerate(sections):
            self.cell(10, 7, f'{num}.', align='R')
            self.cell(0, 7, f'  {title}')
            self.ln()

    def h1(self, text):
        self.ln(4)
        self.set_fill_color(79, 70, 229)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 10, f'  {text}', fill=True)
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def h2(self, text):
        self.ln(3)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(79, 70, 229)
        self.cell(0, 8, text)
        self.ln(2)
        self.set_draw_color(199, 210, 254)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def h3(self, text):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(30, 30, 30)
        self.cell(0, 7, text)
        self.ln(4)

    def body(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def code(self, text):
        self.set_fill_color(245, 245, 250)
        self.set_draw_color(210, 210, 220)
        self.set_font('Courier', '', 8)
        self.set_text_color(30, 30, 90)
        lines = text.strip().split('\n')
        self.ln(2)
        padding = 4
        h = 4.5
        total_h = len(lines) * h + padding * 2
        x = self.get_x()
        y = self.get_y()
        self.rect(x, y, 170, total_h, 'FD')
        self.set_xy(x + padding, y + padding)
        for line in lines:
            self.cell(162, h, line[:100])
            self.ln(h)
        self.set_xy(x, y + total_h + 2)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def bullet(self, items):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(50, 50, 50)
        for item in items:
            x = self.get_x()
            self.cell(6, 5.5, '-')
            self.multi_cell(164, 5.5, item)
        self.ln(2)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            w = 170 // len(headers)
            col_widths = [w] * len(headers)
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(237, 233, 254)
        self.set_text_color(55, 48, 163)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True)
        self.ln()
        self.set_font('Helvetica', '', 9)
        self.set_text_color(30, 30, 30)
        for ri, row in enumerate(rows):
            fill = ri % 2 == 0
            self.set_fill_color(249, 250, 251) if fill else self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell)[:35], border=1, fill=True)
            self.ln()
        self.ln(3)

    def info_box(self, text, color=(237, 233, 254)):
        self.set_fill_color(*color)
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(55, 48, 163)
        self.multi_cell(0, 5.5, text, fill=True)
        self.ln(3)
        self.set_text_color(0, 0, 0)


def build():
    pdf = Doc()


    # -- PORTADA --------------------------------------------------------------
    pdf.cover()

    # -- ÍNDICE ---------------------------------------------------------------
    sections = [
        ('1', 'Vision General del Proyecto'),
        ('2', 'Stack Tecnologico'),
        ('3', 'Arquitectura e Infraestructura (Docker)'),
        ('4', 'Modelo de Datos (Base de Datos)'),
        ('5', 'Agente Principal - AgentExecutor'),
        ('6', 'Tool Calling & Herramientas del Agente'),
        ('7', 'RAG - Retrieval Augmented Generation'),
        ('8', 'Sistema de Metricas (LLM Tracker)'),
        ('9', 'Historial de Conversacion'),
        ('10', 'MCP - Model Context Protocol'),
        ('11', 'Agentes Proactivos (Scheduler)'),
        ('12', 'Consejo Pyme - Multi-Agent Debate'),
        ('13', 'Frontend y Rutas Web'),
        ('14', 'Flujos Criticos End-to-End'),
        ('15', 'Escalabilidad y Decisiones de Diseno'),
    ]
    pdf.toc_page(sections)

    # =======================================================================
    # 1. VISIÓN GENERAL
    # =======================================================================
    pdf.add_page()
    pdf.h1('1. Vision General del Proyecto')
    pdf.body(
        'Ticketia Pro es una plataforma SaaS de inteligencia artificial diseñada para pequeñas y medianas empresas (PYMEs). '
        'Su objetivo es proporcionar un asistente conversacional multimodal capaz de gestionar citas, generar presupuestos, '
        'producir material de marketing, analizar tickets/facturas y ofrecer asesoramiento empresarial mediante un consejo '
        'virtual de tres agentes IA con personalidades diferenciadas.\n\n'
        'La arquitectura sigue el patron RAG (Retrieval-Augmented Generation) con pgvector, orquestacion de herramientas '
        'mediante OpenAI Function Calling, y agentes proactivos autonomos que se ejecutan diariamente en background.'
    )

    pdf.h2('Capacidades Principales')
    pdf.bullet([
        'Chat conversacional por texto y voz (Whisper STT) con memoria de sesion',
        'Generacion de presupuestos PDF a partir de voz, texto o imagen (GPT-4o Vision)',
        'Agenda inteligente: reserva de citas por lenguaje natural con verificacion de conflictos',
        'Generacion de material de marketing: imagenes (DALL-E 3), presentaciones (PPTX), video (Runway Gen-3)',
        'Base de conocimiento vectorial (RAG + pgvector): documentos PDF/TXT indexados y consultables semanticamente',
        'Consejo Pyme: debate estructurado entre 3 agentes IA con roles diferenciados',
        'Agentes proactivos: Grant Hunter, Business Health Coach, Networker, Post-Sales, Marketing',
        'Metricas de uso LLM: tokens, coste estimado, latencia, tasa de exito por modelo y stage',
        'PWA con notificaciones Web Push y soporte de audio en movil',
    ])

    pdf.h2('Modulos del Proyecto')
    pdf.table(
        ['Modulo', 'Ubicacion', 'Responsabilidad'],
        [
            ['AgentExecutor', 'modules/agents/manager.py', 'Orquestador principal: RAG + tools + LLM'],
            ['CalendarTools', 'modules/agents/tools.py', 'Gestion de citas en BD'],
            ['EmbeddingsService', 'modules/services/embeddings.py', 'RAG: ingesta, chunking, retrieval'],
            ['LLMTracker', 'core/llm_tracker.py', 'Metricas de coste y latencia'],
            ['CouncilManager', 'modules/council/orchestrator.py', 'Debate multi-agente (3 personas)'],
            ['MCPClient', 'core/mcp_client.py', 'Cliente Model Context Protocol (SSE)'],
            ['Scheduler', 'run_scheduler.py', 'Agentes proactivos (cron diario)'],
            ['HistoryService', 'modules/agents/history.py', 'Ventana de contexto (50 msgs)'],
        ],
        [55, 65, 55]
    )

    # =======================================================================
    # 2. STACK TECNOLÓGICO
    # =======================================================================
    pdf.add_page()
    pdf.h1('2. Stack Tecnologico')

    pdf.h2('Backend')
    pdf.table(
        ['Tecnologia', 'Version', 'Uso'],
        [
            ['Python', '3.11', 'Lenguaje principal'],
            ['Flask', '3.x', 'Framework web (blueprints, sesiones, rutas)'],
            ['Flask-SQLAlchemy', '3.x', 'ORM para PostgreSQL/SQLite'],
            ['Gunicorn + gevent', '25.x', 'WSGI server con workers async'],
            ['APScheduler', '3.x', 'Tareas programadas (cron diario)'],
            ['Flask-Limiter', '4.x', 'Rate limiting por IP'],
            ['Flask-Mail', '0.10', 'Envio de emails via SMTP'],
            ['pywebpush', 'latest', 'Notificaciones Web Push (VAPID)'],
        ],
        [50, 30, 95]
    )

    pdf.h2('Inteligencia Artificial')
    pdf.table(
        ['Modelo / API', 'Proveedor', 'Uso en el proyecto'],
        [
            ['GPT-4o', 'OpenAI', 'Chat, vision, orquestacion de tools, council'],
            ['text-embedding-3-small', 'OpenAI', 'Vectorizacion para RAG (1536 dims)'],
            ['DALL-E 3', 'OpenAI', 'Generacion de imagenes de marketing'],
            ['Whisper-1', 'OpenAI', 'Transcripcion de audio a texto (STT)'],
            ['Gen3a Turbo', 'Runway ML', 'Generacion de video (2-stage pipeline)'],
            ['DuckDuckGo Search', 'DDGS', 'Busqueda web para agentes (sin API key)'],
        ],
        [55, 35, 85]
    )

    pdf.h2('Infraestructura y Base de Datos')
    pdf.table(
        ['Componente', 'Tecnologia', 'Rol'],
        [
            ['Base de datos', 'PostgreSQL 15 + pgvector', 'Datos relacionales + busqueda vectorial'],
            ['Contenedores', 'Docker Compose (4 servicios)', 'web, db, mcp-sse, scheduler'],
            ['ORM', 'SQLAlchemy', 'Modelos Python -> tablas SQL'],
            ['Busqueda vectorial', 'pgvector (cosine distance)', 'RAG similarity search'],
            ['PDF', 'FPDF + reportlab', 'Generacion documentos PDF'],
            ['Presentaciones', 'python-pptx', 'Generacion archivos .pptx'],
        ],
        [45, 60, 70]
    )

    pdf.h2('Frontend')
    pdf.bullet([
        'Jinja2 templates (renderizado server-side)',
        'Tailwind CSS (via CDN) - sistema de diseno utility-first',
        'JavaScript vanilla - chat widget, audio recording, SSE events',
        'FullCalendar 6 (CDN) - calendario visual de citas',
        'Chart.js - graficas de metricas LLM',
        'PWA (Service Worker, Web App Manifest) - instalable en movil',
    ])

    # =======================================================================
    # 3. ARQUITECTURA E INFRAESTRUCTURA
    # =======================================================================
    pdf.add_page()
    pdf.h1('3. Arquitectura e Infraestructura (Docker)')

    pdf.h2('Docker Compose - 4 Servicios')
    pdf.body('El proyecto se despliega con Docker Compose. Cada servicio es independiente y se comunica por red interna Docker.')

    pdf.table(
        ['Servicio', 'Imagen / Comando', 'Puerto', 'Rol'],
        [
            ['ticketia_db', 'pgvector/pgvector:pg15', '5432', 'PostgreSQL + extension pgvector'],
            ['ticketia_mcp', 'python mcp_server_sse.py', '8001', 'Servidor MCP SSE (tools compartidas)'],
            ['ticketia_app', '/app/entrypoint.sh', '5000', 'Flask + Gunicorn (2 workers)'],
            ['ticketia_scheduler', 'python run_scheduler.py', '-', 'Agentes proactivos (cron)'],
        ],
        [38, 55, 22, 60]
    )

    pdf.h2('Dependencias entre Servicios')
    pdf.code(
        'db (PostgreSQL) -- healthcheck: pg_isready\n'
        '    |\n'
        '    +-- mcp (starts after db healthy)\n'
        '    |       MCP_SSE_URL=http://mcp:8001/sse\n'
        '    |\n'
        '    +-- web (starts after db healthy + mcp started)\n'
        '    |       DATABASE_URL=postgresql://postgres:password@db:5432/ticketia_db\n'
        '    |\n'
        '    +-- scheduler (starts after db healthy + web started)\n'
        '            Cron: ejecuta run_daily_tasks() cada dia a las 09:00'
    )

    pdf.h2('entrypoint.sh - Startup Seguro')
    pdf.body('El script de arranque ejecuta db.create_all() UNA sola vez antes de lanzar Gunicorn, '
             'evitando race conditions cuando multiples workers arrancan simultaneamente.')
    pdf.code(
        '#!/bin/sh\n'
        'python -c "from app import app, db; app.app_context().__enter__(); db.create_all()"\n'
        'exec gunicorn -w 2 -b 0.0.0.0:5000 --timeout 300 app:app'
    )

    pdf.h2('Volumenes Persistentes')
    pdf.bullet([
        'pgdata - Base de datos PostgreSQL (nunca se pierde al reiniciar)',
        'uploads_data - Imagenes de tickets y documentos subidos por usuarios',
        'generated_docs - PDFs, imagenes, presentaciones y videos generados por IA',
    ])

    # =======================================================================
    # 4. MODELO DE DATOS
    # =======================================================================
    pdf.add_page()
    pdf.h1('4. Modelo de Datos (Base de Datos)')

    pdf.h2('BusinessProfile - Usuario/Empresa')
    pdf.table(
        ['Campo', 'Tipo', 'Descripcion'],
        [
            ['user_phone', 'String(20) PK', 'Identificador unico (telefono)'],
            ['email', 'String(120) unique', 'Credencial de login'],
            ['business_name', 'String(100)', 'Nombre comercial del negocio'],
            ['password_hash', 'String(200)', 'Hash bcrypt de la contrasena'],
            ['plan_tier', 'String(20)', 'BASIC | PRO | ENTERPRISE'],
            ['features', 'JSON', '{"tickets_allowed": true, "bot_enabled": false}'],
            ['system_prompt', 'Text', 'Instrucciones del agente IA (wizard)'],
            ['static_knowledge', 'JSON', 'sector, servicios, horario, tono, pagos...'],
            ['active_agents', 'JSON', '["grant_hunter", "networker", ...]'],
            ['agent_config', 'JSON', '{"post_sales": {"allow_refunds": true}}'],
            ['push_subscription', 'Text', 'JSON PushSubscription para Web Push'],
        ],
        [42, 38, 90]
    )

    pdf.h2('Appointment - Citas')
    pdf.table(
        ['Campo', 'Tipo', 'Descripcion'],
        [
            ['business_phone', 'String(20) FK', 'Propietario del calendario'],
            ['date', 'Date', 'Fecha de la cita (YYYY-MM-DD)'],
            ['time', 'String(10)', 'Hora en formato HH:MM'],
            ['client_name', 'String(100)', 'Nombre cliente (opcional)'],
            ['client_phone', 'String(20)', 'Telefono cliente (opcional)'],
        ],
        [42, 28, 100]
    )
    pdf.info_box('Restriccion: no pueden existir dos citas con el mismo (business_phone, date, time). '
                 'La verificacion se hace en CalendarTools.book_appointment() antes del INSERT.')

    pdf.h2('KnowledgeChunk - Embeddings RAG')
    pdf.table(
        ['Campo', 'Tipo', 'Descripcion'],
        [
            ['user_phone', 'String(20)', 'Propietario del chunk'],
            ['source_type', 'String(50)', '"wizard" | "document"'],
            ['source_name', 'String(255)', 'Nombre campo wizard o nombre del fichero'],
            ['content', 'Text', 'Fragmento de texto (~1600 chars con 400 de overlap)'],
            ['embedding', 'Vector(1536)', 'Embedding de text-embedding-3-small'],
        ],
        [42, 30, 98]
    )

    pdf.h2('LLMCall - Metricas de IA')
    pdf.table(
        ['Campo', 'Descripcion'],
        [
            ['model', 'gpt-4o | gpt-4o-mini | dall-e-3 | whisper-1 | gen3a_turbo'],
            ['stage', 'chat_main | chat_tool_followup | council_opinion | runway_video...'],
            ['prompt_tokens / completion_tokens', 'Tokens de entrada y salida'],
            ['latency_ms', 'Milisegundos de respuesta'],
            ['cost_usd', 'Coste estimado calculado segun tabla PRICING'],
            ['success', 'True si la llamada tuvo exito, False si fallo'],
        ],
        [80, 90]
    )

    pdf.h2('Otros Modelos')
    pdf.table(
        ['Modelo', 'Proposito'],
        [
            ['Ticket', 'Facturas/gastos: imagen, concepto, total, NIF, proveedor, base, IVA'],
            ['ChatMessage', 'Historial conversacion: role (user/assistant/tool), content, tool_call_id'],
            ['Grant', 'Ayudas y subvenciones: titulo, sector, importe, deadline, notified_phones'],
            ['SynergyMatch', 'Matches B2B entre empresas: user_a, user_b, score (0-100), reason'],
            ['Notification', 'Notificaciones in-app: titulo, mensaje, type, is_read'],
            ['ActivityLog', 'Registro de acciones de agentes: agent_name, action, timestamp'],
            ['GeneratedDocument', 'Docs generados (PDF, imagen, PPT, video): file_path, doc_type'],
            ['Incident', 'Incidencias de postventa: order_id, type, status, description'],
        ],
        [50, 120]
    )

    # =======================================================================
    # 5. AGENTE PRINCIPAL - AGENTEXECUTOR
    # =======================================================================
    pdf.add_page()
    pdf.h1('5. Agente Principal - AgentExecutor')

    pdf.body(
        'AgentExecutor es el cerebro de la plataforma. Recibe el mensaje del usuario (texto o transcripcion de audio), '
        'enriquece el contexto con RAG, ejecuta el ciclo de tool calling con GPT-4o y devuelve la respuesta final. '
        'Se instancia en cada peticion HTTP y no mantiene estado entre requests (stateless por diseno).'
    )

    pdf.h2('Pipeline execute() - 6 Pasos')
    pdf.code(
        'def execute():\n'
        '  # 1. Si hay imagen y agente admin_redactor activo:\n'
        '  if media_url and "admin_redactor" in active_agents:\n'
        '      return _handle_image_direct_processing()\n\n'
        '  # 2. Guardar mensaje del usuario en BD\n'
        '  HistoryService.save_interaction(phone, "user", user_message)\n\n'
        '  # 3. Construir contexto: historial + RAG\n'
        '  history = HistoryService.get_recent_history(phone, limit=10)\n'
        '  rag_prompt = _build_rag_system_prompt(user_message)\n'
        '  messages = [{"role": "system", "content": rag_prompt}] + history\n\n'
        '  # 4. Primera llamada al LLM\n'
        '  response = client.chat.completions.create(\n'
        '      model="gpt-4o", messages=messages,\n'
        '      tools=TOOLS_SCHEMA, tool_choice="auto"\n'
        '  )\n'
        '  track(phone, "gpt-4o", "chat_main", response, latency_ms)\n\n'
        '  # 5. Si el LLM quiere ejecutar una herramienta:\n'
        '  if response.choices[0].finish_reason == "tool_calls":\n'
        '      return _process_tool_calls(messages, tool_calls)\n\n'
        '  # 6. Guardar y devolver respuesta directa\n'
        '  HistoryService.save_interaction(phone, "assistant", content)\n'
        '  return content'
    )

    pdf.h2('Enriquecimiento RAG del System Prompt')
    pdf.body('Antes de cada llamada al LLM, el system prompt se enriquece dinamicamente con:')
    pdf.bullet([
        'Fecha y hora actual (para que el agente interprete fechas relativas correctamente)',
        'Top-5 chunks mas relevantes de la base de conocimiento vectorial (cosine similarity)',
        'Si RAG falla: se usa el system prompt base sin contexto adicional (fallback graceful)',
    ])
    pdf.code(
        'today = datetime.now().strftime("%A, %d de %B de %Y")\n'
        'base = f"{system_prompt}\\n\\nFecha actual: {today}"\n\n'
        'chunks = retrieve_chunks(phone, user_message, top_k=5)\n'
        'if chunks:\n'
        '    context = "\\n".join(f"- {c}" for c in chunks)\n'
        '    return f"{base}\\n\\nCONTEXTO RELEVANTE:\\n{context}"'
    )

    pdf.h2('Segunda Llamada al LLM (Tool Followup)')
    pdf.body(
        'Cuando el agente ejecuta una tool, el resultado se agrega al historial de mensajes '
        'y se hace una segunda llamada al LLM SIN tools disponibles. Esto obliga al modelo '
        'a formular la respuesta final en lenguaje natural usando el resultado obtenido.'
    )
    pdf.code(
        '# Despues de ejecutar todas las tools:\n'
        'messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})\n\n'
        '# Segunda llamada para sintetizar\n'
        'final = client.chat.completions.create(model="gpt-4o", messages=messages)\n'
        'track(phone, "gpt-4o", "chat_tool_followup", final, latency_ms)\n'
        'return final.choices[0].message.content'
    )

    # =======================================================================
    # 6. TOOL CALLING & HERRAMIENTAS
    # =======================================================================
    pdf.add_page()
    pdf.h1('6. Tool Calling y Herramientas del Agente')

    pdf.body(
        'El patron de Tool Calling (Function Calling de OpenAI) permite que el LLM decida autonomamente '
        'cuando necesita ejecutar una accion del mundo real. El desarrollador define el contrato JSON '
        '(schema) de cada herramienta; el modelo rellena los argumentos y devuelve una llamada estructurada. '
        'Anadir una herramienta nueva no requiere modificar el orquestador: solo hay que registrar '
        'el schema en TOOLS_SCHEMA y el handler en _process_tool_calls().'
    )

    pdf.h2('Herramientas Disponibles')
    pdf.table(
        ['Herramienta', 'Parametros Requeridos', 'Funcion Python'],
        [
            ['check_availability', 'date (YYYY-MM-DD)', 'CalendarTools.check_availability()'],
            ['book_appointment', 'date, time', 'CalendarTools.book_appointment()'],
            ['create_proposal_from_last_image', 'ninguno', '_tool_create_proposal_from_last_image()'],
            ['create_proposal_from_text', 'client_name, items, total', '_tool_create_proposal_from_text()'],
            ['generate_marketing_material', 'prompt, format', '_tool_generate_marketing()'],
            ['handle_customer_service', 'issue_summary', 'PostSalesAgent.handle_inquiry()'],
        ],
        [58, 45, 72]
    )

    pdf.h2('Ejemplo: Schema JSON de book_appointment')
    pdf.code(
        '{\n'
        '  "type": "function",\n'
        '  "function": {\n'
        '    "name": "book_appointment",\n'
        '    "description": "Reserva una cita. Solo fecha y hora son obligatorios.",\n'
        '    "parameters": {\n'
        '      "type": "object",\n'
        '      "properties": {\n'
        '        "date":        {"type": "string", "description": "YYYY-MM-DD"},\n'
        '        "time":        {"type": "string", "description": "HH:MM"},\n'
        '        "client_name": {"type": "string", "description": "Opcional"},\n'
        '        "phone":       {"type": "string", "description": "Opcional"}\n'
        '      },\n'
        '      "required": ["date", "time"]\n'
        '    }\n'
        '  }\n'
        '}'
    )

    pdf.h2('Flujo completo de Tool Execution')
    pdf.code(
        'Usuario: "Reserva el viernes a las 10"\n\n'
        '-> LLM#1 decide: finish_reason = "tool_calls"\n'
        '   tool_calls = [{\n'
        '     "name": "book_appointment",\n'
        '     "arguments": {"date": "2026-04-24", "time": "10:00"}\n'
        '   }]\n\n'
        '-> Python ejecuta: CalendarTools.book_appointment(\n'
        '     date="2026-04-24", time="10:00",\n'
        '     business_phone=user_phone, client_name="", phone=""\n'
        '   )\n'
        '   -> result = "Cita confirmada para el 2026-04-24 a las 10:00."\n\n'
        '-> messages.append({"role": "tool", "content": result, ...})\n\n'
        '-> LLM#2 sintetiza:\n'
        '   "Listo! He reservado el viernes 24 de abril a las 10:00. \u00bfNecesitas algo mas?"'
    )

    pdf.h2('Escalabilidad del sistema de tools')
    pdf.body(
        'Anadir una nueva capacidad al agente requiere solo 3 pasos:\n'
        '1. Definir el schema JSON en TOOLS_SCHEMA (contrato de parametros)\n'
        '2. Implementar la funcion Python que ejecuta la logica\n'
        '3. Agregar un elif en _process_tool_calls()\n\n'
        'El LLM aprende a usar la herramienta solo por la descripcion del schema, sin reentrenamiento.'
    )

    # =======================================================================
    # 7. RAG - RETRIEVAL AUGMENTED GENERATION
    # =======================================================================
    pdf.add_page()
    pdf.h1('7. RAG - Retrieval Augmented Generation')

    pdf.body(
        'El sistema RAG permite al agente consultar documentos propios del negocio en tiempo real. '
        'En lugar de reentrenar el modelo (costoso e inflexible), los documentos se fragmentan, '
        'se vectorizan con embeddings y se almacenan en pgvector. En cada consulta, los fragmentos '
        'mas similares semanticamente se inyectan en el system prompt del LLM.'
    )

    pdf.h2('Parametros de Chunking')
    pdf.table(
        ['Parametro', 'Valor', 'Justificacion'],
        [
            ['CHUNK_SIZE', '1600 chars (~400 tokens)', 'Sweet spot para text-embedding-3-small; contexto suficiente sin diluir semantica'],
            ['CHUNK_OVERLAP', '400 chars (~100 tokens, 25%)', 'Evita perder informacion en limites de fragmento; rango optimo 20-25%'],
            ['Separadores', r'["\n\n", "\n", ". ", " ", ""]', 'Jerarquico: prioriza parrafos > lineas > frases > palabras > chars'],
            ['Min chunk size', '50 chars', 'Descarta fragmentos demasiado cortos para embedear'],
            ['top_k retrieval', '5 chunks', 'Balance entre contexto relevante y ruido en el prompt'],
        ],
        [35, 50, 85]
    )

    pdf.h2('Algoritmo de Chunking Recursivo')
    pdf.body('A diferencia del chunking fijo por caracteres, el chunking recursivo respeta las unidades semanticas naturales del texto:')
    pdf.code(
        'def _split_text(text, chunk_size=1600, overlap=400):\n'
        '    separators = ["\\n\\n", "\\n", ". ", " ", ""]\n\n'
        '    def _recursive(text, seps):\n'
        '        sep = seps[0]\n'
        '        if not sep:  # Caso base: partir por chars con overlap\n'
        '            while start < len(text):\n'
        '                yield text[start : start+chunk_size]\n'
        '                start += chunk_size - overlap\n'
        '            return\n'
        '        # Caso recursivo: partir por separador\n'
        '        parts = text.split(sep)\n'
        '        current = ""\n'
        '        for part in parts:\n'
        '            candidate = current + sep + part\n'
        '            if len(candidate) <= chunk_size:\n'
        '                current = candidate\n'
        '            else:\n'
        '                yield current\n'
        '                if len(part) > chunk_size:\n'
        '                    yield from _recursive(part, seps[1:])  # bajar nivel\n'
        '                else:\n'
        '                    current = part\n'
        '    # Anadir overlap entre chunks consecutivos\n'
        '    result = list(_recursive(text, separators))\n'
        '    for i, chunk in enumerate(result):\n'
        '        if i > 0: chunk = result[i-1][-overlap:] + " " + chunk\n'
        '    return [c for c in result if len(c) > 50]'
    )

    pdf.h2('Pipeline completo de Ingesta (PDF/TXT)')
    pdf.code(
        'def ingest_document(user_phone, file_path, filename):\n'
        '    # 1. Extraccion de texto\n'
        '    if filename.endswith(".pdf"):\n'
        '        text = pymupdf4llm.to_markdown(file_path)  # preserva estructura\n'
        '    else:\n'
        '        text = open(file_path).read()\n\n'
        '    # 2. Chunking recursivo\n'
        '    chunks = _split_text(text)  # lista de strings\n\n'
        '    # 3. Embeddings + guardado\n'
        '    for chunk in chunks:\n'
        '        vector = embed_text(chunk)  # list[float] * 1536\n'
        '        db.session.add(KnowledgeChunk(\n'
        '            user_phone=user_phone,\n'
        '            source_type="document",\n'
        '            source_name=filename,\n'
        '            content=chunk,\n'
        '            embedding=vector\n'
        '        ))\n'
        '    db.session.commit()'
    )

    pdf.h2('Retrieval por Similitud Coseno (pgvector)')
    pdf.code(
        'def retrieve_chunks(user_phone, query, top_k=5):\n'
        '    # Evitar embedding de query si no hay chunks\n'
        '    if KnowledgeChunk.query.filter_by(user_phone=user_phone).count() == 0:\n'
        '        return []\n\n'
        '    query_vector = embed_text(query)  # 1536 floats\n\n'
        '    results = (\n'
        '        KnowledgeChunk.query\n'
        '        .filter_by(user_phone=user_phone)\n'
        '        .order_by(KnowledgeChunk.embedding.cosine_distance(query_vector))\n'
        '        .limit(top_k)\n'
        '        .all()\n'
        '    )\n'
        '    return [r.content for r in results]  # top 5 fragmentos'
    )

    pdf.info_box(
        'Distancia coseno en pgvector: valores entre 0 (identicos) y 2 (opuestos). '
        'Un umbral tipico de relevancia es < 0.5. pgvector usa el operador <=> para la distancia coseno, '
        'aprovechando indices HNSW o IVFFlat para busquedas sublineales en colecciones grandes.'
    )

    # =======================================================================
    # 8. MÉTRICAS - LLM TRACKER
    # =======================================================================
    pdf.add_page()
    pdf.h1('8. Sistema de Metricas (LLM Tracker)')

    pdf.body(
        'El LLMTracker registra automaticamente cada llamada a modelos de IA con tokens consumidos, '
        'latencia, coste estimado y resultado. Los datos se persisten en la tabla LLMCall y '
        'se visualizan en la pagina /metrics con graficas de Chart.js.'
    )

    pdf.h2('Tabla de Precios (Abril 2025)')
    pdf.table(
        ['Modelo', 'Coste Input', 'Coste Output', 'Unidad'],
        [
            ['gpt-4o', '$2.50', '$10.00', 'por 1M tokens'],
            ['gpt-4o-mini', '$0.15', '$0.60', 'por 1M tokens'],
            ['dall-e-3', '$0.040', '-', 'por imagen 1024x1024'],
            ['whisper-1', '$0.006', '-', 'por minuto de audio'],
            ['gen3a_turbo', '$0.050', '-', 'por segundo de video (~$0.25/video 5s)'],
        ],
        [42, 30, 30, 68]
    )

    pdf.h2('Context Manager timed_track()')
    pdf.body('El context manager mide latencia automaticamente y llama a track() en el bloque finally:')
    pdf.code(
        'with timed_track(user_phone, "gpt-4o", "chat_main") as t:\n'
        '    response = client.chat.completions.create(...)\n'
        '    t["response"] = response  # necesario para extraer tokens\n\n'
        '# timed_track.finally() calcula latency_ms y llama a:\n'
        '# track(user_phone, model, stage, response, latency_ms, success)'
    )

    pdf.h2('Metricas Disponibles en /metrics')
    pdf.bullet([
        'KPIs: coste total acumulado, tokens totales, latencia media, tasa de exito',
        'Grafica: llamadas diarias (ultimos 14 dias) - Chart.js line chart',
        'Distribucion por modelo: pie chart con porcentaje de uso',
        'Coste por modelo: bar chart comparativo',
        'Tabla detallada por stage (chat_main, council_opinion, etc.)',
        'Vista admin: agrega metricas de TODOS los usuarios (solo admin@ticketia.com)',
    ])

    # =======================================================================
    # 9. HISTORIAL DE CONVERSACIÓN
    # =======================================================================
    pdf.add_page()
    pdf.h1('9. Historial de Conversacion')

    pdf.body(
        'HistoryService gestiona la ventana de contexto del agente. Los mensajes se persisten '
        'en la tabla ChatMessage y se recuperan en orden cronologico para construir el contexto '
        'de cada llamada al LLM. Un mecanismo de auto-cleanup mantiene la ventana acotada.'
    )

    pdf.h2('Parametros')
    pdf.table(
        ['Constante', 'Valor', 'Proposito'],
        [
            ['MAX_HISTORY', '50 mensajes', 'Threshold que dispara el cleanup automatico'],
            ['KEEP_COUNT', '40 mensajes', 'Mensajes que se conservan tras el cleanup'],
            ['limit (get_recent_history)', '10 mensajes', 'Mensajes que se pasan al LLM en cada peticion'],
        ],
        [40, 35, 95]
    )

    pdf.h2('Auto-cleanup')
    pdf.code(
        'def save_interaction(phone, role, content, ...):\n'
        '    db.session.add(ChatMessage(...))\n'
        '    count = ChatMessage.query.filter_by(user_phone=phone).count() + 1\n'
        '    if count > MAX_HISTORY:  # > 50\n'
        '        to_delete = count - KEEP_COUNT  # cuantos borrar\n'
        '        oldest = (ChatMessage.query\n'
        '            .filter_by(user_phone=phone)\n'
        '            .order_by(created_at.asc())\n'
        '            .limit(to_delete).all())\n'
        '        for msg in oldest:\n'
        '            db.session.delete(msg)\n'
        '    db.session.commit()'
    )

    pdf.info_box(
        'CRITICO: Los mensajes de role="tool" DEBEN incluir los campos "name" y "tool_call_id" '
        'para cumplir el formato de la API de OpenAI. La ausencia de estos campos causa un error 400 '
        'en la segunda llamada al LLM. ChatMessage tiene columnas nullable para estos campos.'
    )

    # =======================================================================
    # 10. MCP - MODEL CONTEXT PROTOCOL
    # =======================================================================
    pdf.add_page()
    pdf.h1('10. MCP - Model Context Protocol')

    pdf.body(
        'MCP (Model Context Protocol) es un estandar abierto de Anthropic para conectar LLMs '
        'con herramientas externas de forma estandarizada. Ticketia lo usa para exponer tools '
        'de negocio (finanzas, agenda, email, estadisticas) que consumen el CouncilManager '
        'y otros agentes de forma desacoplada del agente principal.'
    )

    pdf.h2('Arquitectura MCP en el proyecto')
    pdf.table(
        ['Componente', 'Fichero', 'Rol'],
        [
            ['Servidor MCP SSE', 'mcp_server_sse.py', 'Expone tools via HTTP/SSE en puerto 8001'],
            ['Servidor MCP stdio', 'mcp_server.py', 'Fallback local: tools via stdin/stdout'],
            ['Cliente MCP', 'core/mcp_client.py', 'Descubre y ejecuta tools del servidor'],
            ['Tools MCP', 'core/mcp_tools.py', 'Implementacion Python de las 6 tools'],
        ],
        [45, 55, 75]
    )

    pdf.h2('6 Tools expuestas por MCP')
    pdf.bullet([
        'get_financial_summary(user_phone) - resumen de tickets y gastos',
        'get_appointments(owner_phone, days_ahead) - proximas citas',
        'search_web(query, max_results) - busqueda DuckDuckGo',
        'schedule_appointment(owner_phone, date, time, client_name, client_phone) - agendar cita',
        'send_email_notification(owner_phone, to_email, subject, body) - enviar email',
        'get_business_stats(owner_phone) - metricas agregadas del negocio',
    ])

    pdf.h2('Transporte: SSE vs stdio')
    pdf.code(
        'class TicketiaMCPClient:\n'
        '    def execute_agent_loop(self, prompt, user_message):\n'
        '        if self._sse_url:  # Docker: MCP_SSE_URL definida\n'
        '            return self._run_with_sse(prompt, user_message)  # ~5ms latencia\n'
        '        else:             # Desarrollo local\n'
        '            return self._run_with_stdio(prompt, user_message)  # ~500ms (fork)'
    )

    pdf.h2('Ciclo de ejecucion MCP (_agent_loop)')
    pdf.code(
        'async def _agent_loop(session, system_prompt, user_message):\n'
        '    # 1. Descubrir tools disponibles en el servidor MCP\n'
        '    tools_result = await session.list_tools()\n'
        '    openai_tools = [convert_to_openai_schema(t) for t in tools_result.tools]\n\n'
        '    # 2. Primera llamada LLM con tools MCP\n'
        '    response = await client.chat.completions.create(\n'
        '        model="gpt-4o",\n'
        '        messages=messages,\n'
        '        tools=openai_tools\n'
        '    )\n\n'
        '    # 3. Si hay tool calls, ejecutar via MCP\n'
        '    for tc in tool_calls:\n'
        '        result = await session.call_tool(tc.name, tc.arguments)\n'
        '        messages.append({"role": "tool", "content": result.content, ...})\n\n'
        '    # 4. Segunda llamada para sintetizar resultados\n'
        '    return await client.chat.completions.create(model="gpt-4o", messages=messages)'
    )

    # =======================================================================
    # 11. AGENTES PROACTIVOS
    # =======================================================================
    pdf.add_page()
    pdf.h1('11. Agentes Proactivos (Scheduler)')

    pdf.body(
        'Los agentes proactivos son modulos autonomos que se ejecutan diariamente a las 09:00 AM '
        'via APScheduler. Cada agente se activa individualmente por usuario desde el Marketplace. '
        'Todos generan notificaciones in-app y/o Web Push al terminar.'
    )

    pdf.h2('Agentes Disponibles')
    pdf.table(
        ['Agente (ID)', 'Clase', 'Frecuencia', 'Funcion Principal'],
        [
            ['grant_hunter', 'GrantHunterAgent', 'Diaria', 'Detecta subvenciones por sector y notifica'],
            ['business_health', 'BusinessCoachAgent', 'Diaria', 'Analiza varianza de ingresos y genera insight'],
            ['networker', 'SynergyAgent', 'Diaria', 'Detecta oportunidades B2B entre usuarios'],
            ['post_sales_service', 'PostSalesAgent', 'Por evento', 'Gestiona devoluciones y quejas de clientes'],
            ['marketing_generator', 'MarketingAgent', 'Por peticion', 'Genera imagenes, PPT y video en background'],
            ['admin_redactor', 'AdminAssistantAgent', 'Por imagen', 'Procesa imagenes -> presupuesto PDF'],
        ],
        [35, 42, 28, 70]
    )

    pdf.h2('Grant Hunter - Subvenciones')
    pdf.code(
        'def check_new_grants(user):\n'
        '    for grant in Grant.query.all():\n'
        '        if user.phone in grant.notified_phones:\n'
        '            continue  # ya notificado\n'
        '        if grant.sector_focus == "General":\n'
        '            match = True\n'
        '        elif user_sector in grant.sector_focus:\n'
        '            match = True\n'
        '        else:\n'
        '            # IA evalua match semantico\n'
        '            match = _ai_match(user_sector, user_location, grant)\n'
        '        if match:\n'
        '            pitch = _generate_pitch(user, grant)  # GPT: 50 palabras\n'
        '            NotificationService.send_in_app(user.phone, titulo, pitch)\n'
        '            NotificationService.send_push(user.phone, titulo, pitch)\n'
        '            grant.notified_phones.append(user.phone)  # no volver a notificar\n'
        '    db.session.commit()'
    )

    pdf.h2('PostSales Agent - Clasificacion de Intenciones')
    pdf.body('El agente de postventa clasifica el mensaje del cliente en 5 categorias y aplica politicas configuradas por el dueno del negocio:')
    pdf.table(
        ['Intencion', 'Politica Aplicada', 'Resultado'],
        [
            ['RETOUR', 'allow_refunds=True', 'Generar etiqueta PDF devolucion'],
            ['RETOUR', 'allow_refunds=False', 'Redirigir a proceso de aprobacion'],
            ['RETOUR', 'forbidden_items match', 'Denegar con explicacion'],
            ['EXCHANGE', 'exchange_url definida', 'Enviar URL de cambio + instrucciones'],
            ['COMPLAINT', 'siempre', 'Alerta urgente al dueno + respuesta empatica'],
            ['STATUS', 'siempre', 'Consultar estado pedido y responder'],
        ],
        [35, 48, 87]
    )

    pdf.h2('Synergy Agent - Networking B2B')
    pdf.body(
        'El agente de networking analiza el perfil de gasto de cada usuario y lo compara con otros usuarios '
        'para detectar sinergias comerciales (cliente-proveedor o alianza estrategica). '
        'Cuando el score IA supera 80/100, crea un SynergyMatch y notifica a ambas partes.'
    )

    # =======================================================================
    # 12. CONSEJO PYME
    # =======================================================================
    pdf.add_page()
    pdf.h1('12. Consejo Pyme - Multi-Agent Debate')

    pdf.body(
        'El Consejo Pyme es un sistema de debate estructurado entre 3 agentes IA con personalidades '
        'diferenciadas. Dado un dilema empresarial, cada agente opina desde su perspectiva, '
        'debaten entre si y finalmente un "Secretario" sintetiza un Plan de Accion. '
        'El resultado se transmite al frontend en tiempo real via Server-Sent Events (SSE).'
    )

    pdf.h2('Las 3 Personas del Consejo')
    pdf.table(
        ['Persona', 'Rol', 'Estilo', 'Objetivo'],
        [
            ['El Socio (Tiger)', 'Growth & Ventas', 'Agresivo, impaciente', 'Maximizar ventas YA'],
            ['El Gestor (Owl)', 'Legal & Fiscal', 'Conservador, tecnico', 'Evitar multas, viabilidad'],
            ['El Coach (Rocket)', 'Productividad', 'Practico, empatico', 'Trabajar menos / mejor'],
        ],
        [38, 35, 38, 59]
    )

    pdf.h2('3 Rondas del Debate + Sintesis')
    pdf.code(
        'async def run_session(topic, user_context):\n\n'
        '    # RONDA 1: opiniones independientes\n'
        '    for persona in [socio, gestor, coach]:\n'
        '        yield {"type": "typing", "agent": persona.id}\n'
        '        opinion = await _get_agent_opinion(persona, topic)\n'
        '        yield {"type": "message", "text": opinion, "round": 1}\n\n'
        '    # RONDA 2: debate, replicas al ver las otras opiniones\n'
        '    yield {"type": "divider", "text": "Debate"}\n'
        '    for persona in [socio, gestor, coach]:\n'
        '        rebuttal = await _get_agent_rebuttal(persona, topic, history)\n'
        '        yield {"type": "message", "text": rebuttal, "round": 2}\n\n'
        '    # RONDA 3: sintesis del Secretario\n'
        '    yield {"type": "divider", "text": "Conclusion"}\n'
        '    plan = await _generate_synthesis(topic, transcript)\n'
        '    yield {"type": "plan", "text": plan}  # Markdown'
    )

    pdf.h2('Prompt de cada Persona')
    pdf.code(
        'prompt = f"""\n'
        '    Eres {persona.name} ({emoji}).\n'
        '    Rol: {persona.role}\n'
        '    Personalidad: {persona.style}\n'
        '    Objetivo: {persona.goal}\n\n'
        '    Contexto del negocio: {user_context}\n'
        '    Dilema: "{topic}"\n\n'
        '    Da tu opinion breve (max 30 palabras).\n'
        '    Sé directo y fiel a tu personalidad.\n'
        '"""'
    )

    pdf.info_box(
        'El CouncilManager usa AsyncOpenAI (cliente async). Las 3 llamadas de cada ronda '
        'se hacen secuencialmente para mantener el drama del debate. Con asyncio.gather() '
        'se podrian paralelizar, pero perderia el efecto de "pensando en tiempo real".'
    )

    # =======================================================================
    # 13. FRONTEND Y RUTAS WEB
    # =======================================================================
    pdf.add_page()
    pdf.h1('13. Frontend y Rutas Web')

    pdf.h2('Paginas Principales')
    pdf.table(
        ['Ruta', 'Template', 'Descripcion'],
        [
            ['/', 'landing.html', 'Landing page publica'],
            ['/dashboard', 'dashboard.html', 'KPIs, tickets recientes, activity log'],
            ['/wizard', 'wizard.html', 'Configuracion del agente (multi-step)'],
            ['/marketplace', 'marketplace.html', 'Activar/desactivar agentes proactivos'],
            ['/knowledge', 'knowledge.html', 'Subir documentos al RAG'],
            ['/agenda', 'agenda.html', 'Calendario visual (FullCalendar 6)'],
            ['/chatbot-cliente', 'chatbot_cliente.html', 'Vista simulada de cliente final'],
            ['/metrics', 'metrics.html', 'Graficas de uso LLM (Chart.js)'],
            ['/documents', 'documents.html', 'Archivos generados por IA'],
            ['/council', 'council.html', 'Consejo Pyme (SSE streaming)'],
            ['/profile', 'profile.html', 'Cambio de contrasena, perfil'],
        ],
        [40, 48, 87]
    )

    pdf.h2('Chat Widget Global (base.html)')
    pdf.body(
        'El widget de chat esta embebido en base.html y se renderiza en TODAS las paginas '
        'cuando el usuario esta autenticado. Es un componente flotante (fixed bottom-right) '
        'que se muestra/oculta con toggleChat(). El envio usa fetch() a POST /api/chat.'
    )

    pdf.h2('Chatbot Cliente (/chatbot-cliente)')
    pdf.body(
        'Pagina dedicada que simula la experiencia de un cliente final interactuando con el bot. '
        'Visualmente diferenciada (full-page, cabecera con nombre del negocio, indicador "En linea"). '
        'Internamente usa el mismo endpoint /api/chat sin cambios en el backend.'
    )

    pdf.h2('Agenda Visual (/agenda)')
    pdf.body('Usa FullCalendar 6 (via CDN, gratuito) con tres vistas: mes, semana y lista. '
             'Los eventos se cargan via GET /agenda/events (JSON). Al clicar una cita se abre '
             'un modal con nombre del cliente, telefono, fecha y hora.')
    pdf.code(
        '# GET /agenda/events\n'
        'appointments = Appointment.query.filter_by(business_phone=user_phone).all()\n'
        'return jsonify([{\n'
        '    "id": a.id,\n'
        '    "title": a.client_name or "Cita",\n'
        '    "start": f"{a.date}T{a.time}:00",\n'
        '    "extendedProps": {"client_phone": a.client_phone or ""}\n'
        '} for a in appointments])'
    )

    pdf.h2('Server-Sent Events (Consejo Pyme)')
    pdf.body(
        'El streaming SSE permite enviar eventos al frontend sin mantener una conexion WebSocket. '
        'Flask usa stream_with_context() + Response(generator, mimetype="text/event-stream"). '
        'El frontend usa EventSource API para recibir y renderizar los eventos en tiempo real.'
    )

    # =======================================================================
    # 14. FLUJOS CRÍTICOS
    # =======================================================================
    pdf.add_page()
    pdf.h1('14. Flujos Criticos End-to-End')

    pdf.h2('Flujo A: Chat por Voz -> Agendar Cita')
    pdf.code(
        '1. Usuario habla: "Agenda una reunion el viernes a las 10"\n'
        '2. POST /upload_web_audio\n'
        '   -> Guardar .webm en /static/uploads/\n'
        '   -> Whisper-1: transcribe -> "Agenda una reunion el viernes a las 10"\n'
        '   -> run_agent(texto, phone, profile)\n\n'
        '3. AgentExecutor.execute()\n'
        '   -> RAG: retrieve_chunks (puede retornar [])\n'
        '   -> LLM#1: gpt-4o, tool_calls=[\n'
        '       {name: "book_appointment",\n'
        '        arguments: {date: "2026-04-24", time: "10:00"}}\n'
        '     ]\n'
        '   -> CalendarTools.book_appointment(date, time, business_phone)\n'
        '      -> Check conflictos\n'
        '      -> INSERT Appointment\n'
        '   -> LLM#2: sintetiza -> "Listo! Reunion agendada el viernes..."\n\n'
        '4. Cita disponible en GET /agenda/events\n'
        '5. FullCalendar la muestra en el calendario'
    )

    pdf.h2('Flujo B: Subida Documento -> RAG')
    pdf.code(
        '1. POST /knowledge/upload (multipart, PDF)\n'
        '2. Guardar en /static/uploads/knowledge/{phone}/\n'
        '3. HTTP Response INMEDIATA: "Indexando..."\n\n'
        '4. [Background Thread]:\n'
        '   -> pymupdf4llm.to_markdown(pdf) -> texto markdown\n'
        '   -> _split_text(texto) -> [chunk1, chunk2, ...] (1600 chars, 25% overlap)\n'
        '   -> Para cada chunk:\n'
        '       embed_text(chunk) -> vector[1536]\n'
        '       INSERT KnowledgeChunk(user_phone, source_name=filename, embedding)\n'
        '   -> commit()\n'
        '   -> NotificationService.send_in_app("Documento indexado: N fragmentos")\n\n'
        '5. Proximo chat del usuario:\n'
        '   retrieve_chunks(phone, query) -> top-5 por cosine distance\n'
        '   Chunks inyectados en system_prompt -> respuesta informada'
    )

    pdf.h2('Flujo C: Consejo Pyme (SSE)')
    pdf.code(
        '1. POST /api/council/stream: {"topic": "Debo abrir sucursal?"}\n'
        '2. CouncilManager().run_session(topic, user_context)\n\n'
        '   RONDA 1 (async, secuencial):\n'
        '   -> yield {type:typing, agent:socio}\n'
        '   -> LLM: "Abre ya. El mercado esta maduro." -> yield {type:message}\n'
        '   -> yield {type:typing, agent:gestor}\n'
        '   -> LLM: "Verifica licencias primero." -> yield {type:message}\n'
        '   -> yield {type:typing, agent:coach}\n'
        '   -> LLM: "Focaliza en sistemas antes de expandir." -> yield {type:message}\n\n'
        '   RONDA 2 (replica leyendo las opiniones anteriores):\n'
        '   -> yield {type:divider}\n'
        '   -> Cada agente ve las 3 opiniones y rebate\n\n'
        '   RONDA 3 (sintesis):\n'
        '   -> yield {type:divider}\n'
        '   -> Secretario: Plan de Accion Markdown\n'
        '   -> yield {type:plan, text:"# Plan\\n1. ..."}\n\n'
        '3. Frontend EventSource renderiza cada evento en tiempo real'
    )

    # =======================================================================
    # 15. ESCALABILIDAD Y DECISIONES DE DISEÑO
    # =======================================================================
    pdf.add_page()
    pdf.h1('15. Escalabilidad y Decisiones de Diseno')

    pdf.h2('Por que es escalable')
    pdf.bullet([
        'Tool Calling desacoplado: anadir una nueva capacidad al agente = definir schema JSON + 1 elif. '
        'El LLM aprende a usarla por la descripcion, sin reentrenamiento.',
        'RAG con pgvector: la busqueda vectorial escala a millones de embeddings con indices HNSW/IVFFlat. '
        'Agregar documentos no requiere cambios en el agente.',
        'Agentes proactivos modulares: cada agente es un modulo independiente activable por usuario. '
        'Anadir un agente nuevo no afecta a los existentes.',
        'Docker Compose: cada servicio (web, db, mcp, scheduler) escala independientemente. '
        'Web puede tener multiples replicas sin tocar la BD.',
        'Costes bajo control: LLMTracker registra cada llamada con coste estimado, '
        'permitiendo detectar optimizaciones (cambiar a gpt-4o-mini en stages de bajo valor).',
    ])

    pdf.h2('Decisiones de Diseno Justificadas')
    pdf.table(
        ['Decision', 'Alternativa Descartada', 'Razon'],
        [
            ['Chunking recursivo 1600/400', 'Chunking fijo por chars', 'Respeta unidades semanticas; 400 tokens es sweet spot para text-embedding-3-small'],
            ['PDF -> Markdown (pymupdf4llm)', 'pypdf texto plano', 'Preserva encabezados y listas; mejora coherencia semantica de cada chunk'],
            ['Overlap 25%', 'Overlap 0% o 50%', '20-25% es el rango optimo documentado: cubre boundaries sin duplicar contexto'],
            ['top_k=5 chunks', 'top_k=1 o top_k=20', '5 fragmentos: contexto suficiente sin diluir el prompt con ruido'],
            ['pgvector cosine', 'BM25, FAISS, ChromaDB', 'Integrado en PostgreSQL (sin infra extra); cosine es robusto para embeddings normalizados'],
            ['Gunicorn sync workers', 'FastAPI async', 'Flask syncrono es mas simple; async solo en Council (AsyncOpenAI)'],
            ['Background threads', 'Celery + Redis', 'Sin infra adicional para el TFM; en produccion real se migraria a Celery'],
            ['SSE vs WebSocket', 'WebSocket', 'SSE es unidireccional (servidor -> cliente): suficiente para streaming, mas simple'],
        ],
        [50, 42, 78]
    )

    pdf.h2('Limitaciones Identificadas (Trabajo Futuro)')
    pdf.bullet([
        'Concurrencia: Gunicorn sync con 2 workers no escala a miles de usuarios concurrentes. '
        'Solucion: migrar llamadas LLM a cola Celery + Redis.',
        'Memoria por cliente externo: el bot no recuerda conversaciones anteriores con el mismo '
        'cliente en sesiones distintas. Solucion: integracion con Mem0 + identificacion del cliente.',
        'Sin streaming en chat: la respuesta del agente se entrega completa al terminar. '
        'Solucion: streaming SSE en el endpoint /api/chat (como ya hace el Council).',
        'Rate limiter en memoria: el limiter se resetea al reiniciar el servidor. '
        'Solucion: backend Redis para persistencia entre reinicios.',
        'Agente sincrono: el agente principal bloquea el worker HTTP durante la llamada LLM. '
        'Solucion: endpoint async con asyncio/gevent.',
    ])

    pdf.h2('Resumen Tecnico Ejecutivo')
    pdf.table(
        ['Aspecto', 'Tecnologia / Valor'],
        [
            ['Lenguaje', 'Python 3.11'],
            ['Framework web', 'Flask 3.x + Gunicorn + gevent'],
            ['Base de datos', 'PostgreSQL 15 + pgvector (Vector(1536))'],
            ['LLM principal', 'GPT-4o (chat, vision, tool calling, council)'],
            ['Modelos secundarios', 'DALL-E 3, Whisper-1, Runway Gen-3, text-embedding-3-small'],
            ['Orquestacion herramientas', 'OpenAI Function Calling + MCP (SSE/stdio)'],
            ['Busqueda vectorial', 'pgvector cosine distance (top_k=5, 1536 dims)'],
            ['Concurrencia', 'Threading (background tasks), AsyncIO (Council)'],
            ['Rate limiting', 'flask-limiter (30 req/min chat, 20 req/h audio)'],
            ['Notificaciones', 'In-app (DB), Web Push (PWA/VAPID), Email (SMTP)'],
            ['Scheduler', 'APScheduler (cron 09:00 diario, contenedor propio)'],
            ['Infraestructura', 'Docker Compose: 4 servicios (web, db, mcp-sse, scheduler)'],
            ['Frontend', 'Jinja2 + Tailwind CSS + JS vanilla + FullCalendar + Chart.js'],
        ],
        [55, 115]
    )

    # -- Guardar --------------------------------------------------------------
    out = os.path.join(os.path.dirname(__file__), 'TICKETIA_PRO_Documentacion_Tecnica_TFM.pdf')
    pdf.output(out)
    print(f'PDF generado: {out}')


if __name__ == '__main__':
    build()
