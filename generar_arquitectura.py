"""
Genera un PDF de arquitectura de Ticketia/Zeptai para la defensa del TFM.
Produce: arquitectura_ticketia.pdf  (A4 apaisado, varias páginas)

Páginas:
  1. Visión general del sistema
  2. Capa de datos — modelos BD y relaciones
  3. Pipeline de agentes IA
  4. Flujo MCP (Council)
  5. Observabilidad LLM (métricas)
  6. Flujo completo de una petición web

Ejecución:
    python generar_arquitectura.py
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

OUT = "arquitectura_ticketia.pdf"

# ── Paleta de colores ──────────────────────────────────────────────────────────
C = {
    "bg":        "#F8F9FA",
    "header":    "#1A1A2E",
    "flask":     "#3B82F6",     # azul
    "db":        "#10B981",     # verde
    "agent":     "#8B5CF6",     # morado
    "external":  "#F59E0B",     # naranja
    "mcp":       "#EF4444",     # rojo
    "user":      "#06B6D4",     # cyan
    "tracker":   "#EC4899",     # rosa
    "arrow":     "#64748B",
    "white":     "#FFFFFF",
    "light":     "#E2E8F0",
    "text_dark": "#1E293B",
    "text_light":"#F1F5F9",
}

def box(ax, x, y, w, h, label, sublabel="", color="#3B82F6", fontsize=8, radius=0.015):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0.005,rounding_size={radius}",
                          facecolor=color, edgecolor="white", linewidth=1.2,
                          zorder=3)
    ax.add_patch(rect)
    cy = y + h / 2
    if sublabel:
        ax.text(x + w/2, cy + h*0.13, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=C["white"], zorder=4)
        ax.text(x + w/2, cy - h*0.18, sublabel, ha='center', va='center',
                fontsize=fontsize-1.5, color=C["text_light"], zorder=4, style='italic')
    else:
        ax.text(x + w/2, cy, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=C["white"], zorder=4)

def arrow(ax, x1, y1, x2, y2, color="#64748B", lw=1.2, style="-|>", label="", label_color="#1E293B"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=6,
                color=label_color, zorder=5,
                bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.8, ec='none'))

def dashed_arrow(ax, x1, y1, x2, y2, color="#64748B", lw=1.0, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle='dashed', connectionstyle='arc3,rad=0'),
                zorder=2)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my, label, ha='center', va='bottom', fontsize=6, color=color,
                bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.8, ec='none'))

def title_page(ax, title, subtitle=""):
    ax.set_facecolor(C["header"])
    ax.text(0.5, 0.58, title, ha='center', va='center', fontsize=22,
            fontweight='bold', color='white', transform=ax.transAxes)
    if subtitle:
        ax.text(0.5, 0.42, subtitle, ha='center', va='center', fontsize=11,
                color='#94A3B8', transform=ax.transAxes, style='italic')
    ax.text(0.5, 0.18, "Alejandro Brata · TFM · 2026",
            ha='center', va='center', fontsize=9, color='#64748B',
            transform=ax.transAxes)

def new_ax(pdf, title="", landscape=True):
    fig = plt.figure(figsize=(16, 9) if landscape else (11, 16))
    fig.patch.set_facecolor(C["bg"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_facecolor(C["bg"])
    ax.axis('off')
    if title:
        # cabecera
        hdr = FancyBboxPatch((0, 8.3), 16, 0.7,
                             boxstyle="square,pad=0", facecolor=C["header"],
                             edgecolor='none', zorder=1)
        ax.add_patch(hdr)
        ax.text(0.25, 8.65, title, va='center', fontsize=13,
                fontweight='bold', color='white', zorder=2)
        ax.text(15.75, 8.65, "Ticketia · Zeptai", va='center', ha='right',
                fontsize=8, color='#64748B', zorder=2)
    return fig, ax, pdf


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Visión general
# ══════════════════════════════════════════════════════════════════════════════
def page_overview(pdf):
    fig, ax, _ = new_ax(pdf, "1 · Visión General del Sistema")

    # ── Usuario ──
    box(ax, 0.3, 3.5, 1.8, 1.2, "Usuario /\nAutónomo", "PWA · Móvil · Web", C["user"], 8)

    # ── PWA / Browser ──
    box(ax, 2.7, 3.5, 2.0, 1.2, "PWA / Browser", "Service Worker\nOff-line support", C["flask"], 8)
    arrow(ax, 2.1, 4.1, 2.7, 4.1, C["user"])
    arrow(ax, 2.7, 3.85, 2.1, 3.85, C["user"], label="HTML/JSON")

    # ── Flask App ──
    box(ax, 5.4, 6.4, 2.2, 1.1, "Flask App", "app.py · WSGI", C["flask"], 9)
    box(ax, 5.4, 4.8, 2.2, 1.1, "routes/web.py", "SSR + Session", C["flask"], 8)
    box(ax, 5.4, 3.2, 2.2, 1.1, "routes/api.py", "REST JSON\nRate-limit", C["flask"], 8)

    # flechas PWA → Flask
    arrow(ax, 4.7, 4.5, 5.4, 7.0, C["flask"], label="HTTP")
    arrow(ax, 4.7, 4.1, 5.4, 5.4, C["flask"])
    arrow(ax, 4.7, 3.8, 5.4, 3.8, C["flask"])

    # brace Flask interno
    ax.annotate("", xy=(5.4, 6.45), xytext=(5.4, 4.25),
                arrowprops=dict(arrowstyle="-", color=C["flask"], lw=1))

    # ── AgentExecutor ──
    box(ax, 8.3, 5.5, 2.2, 1.1, "AgentExecutor", "Function Calling\ngpt-4o", C["agent"], 8)
    arrow(ax, 7.6, 3.75, 8.3, 6.0, C["agent"], label="invoke")

    # ── Agentes Proactivos ──
    proactive = [
        ("GrantHunter", 8.1), ("BusinessCoach", 9.2),
        ("Networker", 10.3), ("PostSales", 11.4), ("AdminRedactor", 12.5),
    ]
    box(ax, 8.3, 2.6, 5.0, 0.9, "Agentes Proactivos (Scheduler diario)", "", C["agent"], 8)
    for name, px in proactive:
        box(ax, px-0.45, 1.3, 0.95, 0.9, name, "", C["agent"], 6.5)
        arrow(ax, px, 2.2, px, 2.2, C["agent"])

    arrow(ax, 7.6, 7.0, 8.3, 6.5, C["agent"])

    # ── Council (MCP) ──
    box(ax, 8.3, 7.1, 2.2, 1.0, "CouncilManager", "3 Personas IA\nDebate + Síntesis", C["mcp"], 8)
    arrow(ax, 7.6, 6.9, 8.3, 7.6, C["mcp"], label="council")

    # ── MCP Server ──
    box(ax, 11.1, 7.1, 2.0, 1.0, "MCP Server", "stdio / SSE\n6 tools", C["mcp"], 8)
    arrow(ax, 10.5, 7.6, 11.1, 7.6, C["mcp"], label="MCP protocol")

    # ── OpenAI ──
    box(ax, 11.1, 5.5, 2.0, 1.0, "OpenAI API", "gpt-4o\nDALL-E · Whisper", C["external"], 8)
    arrow(ax, 10.5, 6.0, 11.1, 6.0, C["external"], label="HTTPS")
    arrow(ax, 11.1, 6.4, 10.5, 6.4, C["external"])

    # ── Runway ──
    box(ax, 13.7, 6.35, 2.0, 0.9, "Runway ML", "gen3a_turbo\nImage-to-Video", C["external"], 8)
    arrow(ax, 13.1, 6.0, 13.7, 6.7, C["external"], label="HTTPS")

    # ── BD ──
    box(ax, 11.1, 3.5, 2.0, 1.5, "PostgreSQL /\nSQLite", "SQLAlchemy ORM\n11 modelos", C["db"], 8)
    arrow(ax, 10.5, 3.75, 11.1, 4.0, C["db"], label="SQL")
    arrow(ax, 11.1, 4.5, 10.5, 4.5, C["db"])

    # ── LLM Tracker ──
    box(ax, 13.7, 3.5, 2.0, 1.5, "LLM Tracker", "llm_tracker.py\ncoste · latencia\nLLMCall BD", C["tracker"], 8)
    arrow(ax, 13.1, 6.0, 13.7, 5.0, C["tracker"], label="track()")
    arrow(ax, 13.1, 3.9, 13.7, 4.0, C["tracker"])

    # ── Flask-Mail ──
    box(ax, 13.7, 1.8, 2.0, 0.9, "Flask-Mail\nSMTP Gmail", "", C["external"], 8)
    arrow(ax, 13.1, 3.5, 13.7, 2.5, C["external"], label="email")

    # Leyenda
    items = [
        (C["user"],     "Usuario / Frontend"),
        (C["flask"],    "Flask / HTTP"),
        (C["agent"],    "Agentes IA"),
        (C["mcp"],      "MCP / Council"),
        (C["db"],       "Base de Datos"),
        (C["external"], "APIs Externas"),
        (C["tracker"],  "Observabilidad"),
    ]
    lx, ly = 0.3, 2.5
    for color, label in items:
        rect = FancyBboxPatch((lx, ly), 0.25, 0.25,
                              boxstyle="round,pad=0.02", facecolor=color,
                              edgecolor='none', zorder=3)
        ax.add_patch(rect)
        ax.text(lx + 0.35, ly + 0.12, label, va='center', fontsize=7,
                color=C["text_dark"], zorder=4)
        ly -= 0.38

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Modelos de BD
# ══════════════════════════════════════════════════════════════════════════════
def page_db(pdf):
    fig, ax, _ = new_ax(pdf, "2 · Modelos de Base de Datos y Relaciones")

    def entity(x, y, name, fields, color=C["db"]):
        h = 0.28 * (len(fields) + 1) + 0.15
        # cabecera
        hdr = FancyBboxPatch((x, y + h - 0.38), 2.6, 0.38,
                             boxstyle="round,pad=0.01", facecolor=color,
                             edgecolor='white', linewidth=1, zorder=3)
        ax.add_patch(hdr)
        ax.text(x + 1.3, y + h - 0.19, name, ha='center', va='center',
                fontsize=8, fontweight='bold', color='white', zorder=4)
        # cuerpo
        body = FancyBboxPatch((x, y), 2.6, h - 0.38,
                              boxstyle="round,pad=0.01", facecolor='white',
                              edgecolor=color, linewidth=1.2, zorder=3)
        ax.add_patch(body)
        for i, (pk, fname, ftype) in enumerate(fields):
            fy = y + (h - 0.38) - 0.08 - 0.28 * (i + 1)
            if pk:
                ax.text(x + 0.15, fy, "PK", fontsize=5.5, va='center', zorder=4,
                        color='#F59E0B', fontweight='bold')
            ax.text(x + 0.38, fy, fname, fontsize=6.5, va='center',
                    color=C["text_dark"], zorder=4)
            ax.text(x + 2.45, fy, ftype, fontsize=5.5, va='center',
                    ha='right', color='#94A3B8', zorder=4, style='italic')
        return x + 1.3, y + h  # devuelve centro_x, top_y

    def rel(ax, x1, y1, x2, y2, label="", color=C["db"]):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0),
                    zorder=2)
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my+0.08, label, fontsize=5.5, ha='center',
                    color=color, zorder=5,
                    bbox=dict(boxstyle='round,pad=0.1', fc='white', alpha=0.9, ec='none'))

    # BusinessProfile (centro)
    entity(5.9, 4.8, "BusinessProfile", [
        (True,  "user_phone (PK)",   "str"),
        (False, "email",             "str"),
        (False, "business_name",     "str"),
        (False, "system_prompt",     "text"),
        (False, "active_agents",     "JSON"),
        (False, "plan_tier",         "str"),
        (False, "push_subscription", "text"),
    ], C["flask"])

    entity(0.3, 5.8, "Ticket", [
        (True,  "id",          "int"),
        (False, "user_phone",  "FK"),
        (False, "concept",     "str"),
        (False, "total",       "float"),
        (False, "date",        "datetime"),
        (False, "image_path",  "str"),
    ])
    rel(ax, 2.9, 6.9, 5.9, 6.5, "N:1")

    entity(0.3, 3.2, "Appointment", [
        (True,  "id",             "int"),
        (False, "business_phone", "FK"),
        (False, "date",           "date"),
        (False, "time",           "str"),
        (False, "client_name",    "str"),
    ])
    rel(ax, 2.9, 4.3, 5.9, 5.5, "N:1")

    entity(0.3, 1.0, "ChatMessage", [
        (True,  "id",          "int"),
        (False, "user_phone",  "FK"),
        (False, "role",        "str"),
        (False, "content",     "text"),
        (False, "tool_call_id","str"),
    ])
    rel(ax, 2.9, 2.1, 5.9, 5.2, "N:1")

    entity(9.1, 6.5, "Notification", [
        (True,  "id",         "int"),
        (False, "user_phone", "FK"),
        (False, "title",      "str"),
        (False, "message",    "text"),
        (False, "is_read",    "bool"),
    ])
    rel(ax, 9.1, 7.3, 8.5, 6.8, "N:1")

    entity(9.1, 4.5, "ActivityLog", [
        (True,  "id",         "int"),
        (False, "user_phone", "FK"),
        (False, "agent_name", "str"),
        (False, "action",     "text"),
        (False, "timestamp",  "datetime"),
    ])
    rel(ax, 9.1, 5.2, 8.5, 5.8, "N:1")

    entity(9.1, 2.4, "GeneratedDocument", [
        (True,  "id",          "int"),
        (False, "user_phone",  "FK"),
        (False, "file_path",   "str"),
        (False, "doc_type",    "str"),
        (False, "client_name", "str"),
    ])
    rel(ax, 9.1, 3.1, 8.5, 5.4, "N:1")

    entity(9.1, 0.5, "SynergyMatch", [
        (True,  "id",           "int"),
        (False, "user_a_phone", "FK"),
        (False, "user_b_phone", "FK"),
        (False, "score",        "int"),
        (False, "status",       "str"),
    ])

    entity(12.7, 5.5, "LLMCall", [
        (True,  "id",               "int"),
        (False, "user_phone",       "str"),
        (False, "model",            "str"),
        (False, "stage",            "str"),
        (False, "prompt_tokens",    "int"),
        (False, "completion_tokens","int"),
        (False, "cost_usd",         "float"),
        (False, "latency_ms",       "int"),
        (False, "success",          "bool"),
    ], C["tracker"])

    entity(12.7, 3.0, "Grant", [
        (True,  "id",              "int"),
        (False, "title",           "str"),
        (False, "sector_focus",    "str"),
        (False, "amount",          "str"),
        (False, "deadline",        "str"),
        (False, "notified_phones", "JSON"),
    ], C["agent"])

    entity(12.7, 1.0, "Incident", [
        (True,  "id",          "int"),
        (False, "user_phone",  "FK"),
        (False, "order_id",    "str"),
        (False, "type",        "str"),
        (False, "status",      "str"),
    ])

    # nota ORM
    ax.text(5.9, 0.2, "SQLAlchemy ORM · PostgreSQL (prod) / SQLite (dev) · Flask-SQLAlchemy",
            ha='center', fontsize=7.5, color='#475569', style='italic')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Pipeline de Agentes IA
# ══════════════════════════════════════════════════════════════════════════════
def page_agents(pdf):
    fig, ax, _ = new_ax(pdf, "3 · Pipeline de Agentes IA")

    # ── Scheduler ──
    box(ax, 0.3, 4.0, 2.2, 1.2, "Scheduler\nDiario", "run_daily_tasks()\nAPScheduler / Cron", C["flask"], 8)

    # ── Agentes proactivos ──
    agents_info = [
        ("GrantHunter",    "BOE · Subvenciones\nDDGS search",    2.2, 7.0),
        ("BusinessCoach",  "Salud financiera\nConsejo GPT-4o",   2.2, 5.5),
        ("SynergyAgent",   "Networking\nSynergyMatch BD",        2.2, 4.0),
        ("PostSalesAgent", "Post-venta\nQuejas · Incidencias",   2.2, 2.5),
        ("AdminRedactor",  "Imagen → PDF\nVision + FPDF",        2.2, 1.0),
    ]
    for name, desc, x, y in agents_info:
        box(ax, x, y, 2.4, 1.0, name, desc, C["agent"], 7.5)
        arrow(ax, 2.5, 4.6, x, y + 0.5, C["agent"])

    # ── AgentExecutor (chat) ──
    box(ax, 5.5, 5.0, 2.6, 1.8, "AgentExecutor", "execute()\n_process_tool_calls()\nFunction Calling", C["flask"], 8)

    # Tools disponibles
    tools = [
        ("check_availability",         5.4, 3.6),
        ("book_appointment",           6.7, 3.6),
        ("create_proposal_from_image", 8.0, 3.6),
        ("create_proposal_from_text",  9.3, 3.6),
        ("generate_marketing_material",10.6, 3.6),
        ("handle_customer_service",    11.9, 3.6),
    ]
    box(ax, 5.0, 4.0, 7.8, 0.8, "TOOLS_SCHEMA  (OpenAI Function Calling)", "", "#475569", 7.5)
    for tname, tx, ty in tools:
        box(ax, tx - 0.55, 2.6, 1.25, 0.75, tname, "", C["agent"], 5.5)
        arrow(ax, tx, 3.6, tx, 3.35, C["agent"])

    arrow(ax, 6.8, 5.0, 6.8, 4.8, C["agent"], label="tool_calls")

    # ── GPT-4o calls ──
    box(ax, 9.5, 5.5, 2.4, 1.4, "OpenAI\ngpt-4o", "chat_main\nchat_tool_followup", C["external"], 8)
    arrow(ax, 8.1, 6.0, 9.5, 6.2, C["external"], label="completions")
    arrow(ax, 9.5, 5.8, 8.1, 5.8, C["external"], label="response")

    # ── MarketingAgent (2-stage pipeline) ──
    box(ax, 5.5, 7.2, 2.6, 1.4, "MarketingAgent", "generate_marketing_content()", C["agent"], 8)
    box(ax, 9.5, 7.5, 2.4, 0.6, "Stage 1 · Vision", "Analiza imagen (gpt-4o)", C["external"], 7.5)
    box(ax, 9.5, 6.8, 2.4, 0.6, "Stage 2 · Cinematic", "Genera prompt Runway", C["external"], 7.5)
    box(ax, 12.4, 7.2, 2.4, 0.9, "Runway ML\ngen3a_turbo", "Image-to-Video\nExponential backoff", C["mcp"], 8)
    arrow(ax, 8.1, 7.9, 9.5, 7.8, C["external"])
    arrow(ax, 9.5, 7.5, 9.5, 7.4, C["external"])
    arrow(ax, 11.9, 7.8, 12.4, 7.6, C["mcp"], label="API call")

    # ── LLM Tracker lateral ──
    box(ax, 12.4, 4.8, 2.4, 1.8, "LLM Tracker", "track()\ntimed_track()\nLLMCall → BD", C["tracker"], 8)
    dashed_arrow(ax, 9.5, 6.2, 12.4, 5.6, C["tracker"], label="track()")
    dashed_arrow(ax, 11.9, 7.5, 12.4, 6.5, C["tracker"], label="track()")

    # ── HistoryService ──
    box(ax, 12.4, 3.2, 2.4, 1.2, "HistoryService", "save_interaction()\nget_recent_history()\nChatMessage BD", C["db"], 7.5)
    dashed_arrow(ax, 8.1, 5.5, 12.4, 3.8, C["db"], label="save/load")

    # ── Notif service ──
    box(ax, 12.4, 1.5, 2.4, 1.2, "NotificationService", "create()\nPush Web\nFlask-Mail", C["flask"], 7.5)
    dashed_arrow(ax, 7.8, 2.8, 12.4, 2.1, C["flask"], label="notify")

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — Flujo MCP / Council
# ══════════════════════════════════════════════════════════════════════════════
def page_mcp(pdf):
    fig, ax, _ = new_ax(pdf, "4 · Arquitectura MCP y Council de Asesores")

    # ── Usuario ──
    box(ax, 0.3, 3.8, 1.8, 1.0, "Usuario", "Envía dilema\nde negocio", C["user"], 8)

    # ── API route ──
    box(ax, 2.7, 3.8, 2.0, 1.0, "/api/council\n_stream", "SSE Streaming\nFlask route", C["flask"], 7.5)
    arrow(ax, 2.1, 4.3, 2.7, 4.3, C["user"], label="POST")

    # ── CouncilManager ──
    box(ax, 5.4, 3.0, 2.6, 2.8, "CouncilManager", "run_session()\nRonda 1: Opiniones\nRonda 2: Réplicas\nRonda 3: Síntesis", C["mcp"], 8)
    arrow(ax, 4.7, 4.3, 5.4, 4.4, C["mcp"])

    # ── 3 personas ──
    personas = [
        ("[T] El Socio",   "Growth & Ventas\nAgresivo, ingresos",    5.2, 1.3),
        ("[G] El Gestor",  "Legal & Fiscal\nConservador, riesgos",   7.2, 1.3),
        ("[C] El Coach",   "Productividad\nPractico, tiempo",        9.2, 1.3),
    ]
    for pname, pdesc, px, py in personas:
        box(ax, px, py, 1.9, 1.2, pname, pdesc, C["mcp"], 7)
        arrow(ax, px + 0.95, 3.0, px + 0.95, 2.5, C["mcp"])

    # ── TicketiaMCPClient ──
    box(ax, 5.4, 6.0, 2.6, 1.5, "TicketiaMCPClient", "execute_agent_loop()\n_run_with_sse()\n_run_with_stdio()\n_agent_loop()", C["mcp"], 7.5)
    arrow(ax, 6.7, 5.8, 6.7, 5.5, C["mcp"], label="use_mcp=True")

    # ── Transporte SSE ──
    box(ax, 9.4, 6.8, 2.4, 0.9, "SSE Transport", "mcp_server_sse.py\nport 8001  (Docker)", C["flask"], 7.5)
    # ── Transporte stdio ──
    box(ax, 9.4, 5.7, 2.4, 0.9, "stdio Transport", "mcp_server.py\nsubprocess fallback", C["flask"], 7.5)
    arrow(ax, 8.0, 7.2, 9.4, 7.2, C["flask"], label="SSE preferred")
    dashed_arrow(ax, 8.0, 6.1, 9.4, 6.1, C["flask"], label="stdio fallback")

    # ── MCP Tools ──
    tools_mcp = [
        ("get_financial\n_summary",    10.0, 4.5),
        ("get_appointments",           11.3, 4.5),
        ("search_web\n(DuckDuckGo)",   12.6, 4.5),
        ("schedule\n_appointment",     13.9, 4.5),
        ("send_email\n_notification",  10.0, 3.1),
        ("get_business\n_stats",       11.3, 3.1),
    ]
    box(ax, 9.6, 5.0, 5.0, 0.5, "core/mcp_tools.py  — Fuente única de herramientas", "", "#475569", 7)
    for tname, tx, ty in tools_mcp:
        box(ax, tx, ty, 1.2, 0.9, tname, "", C["db"], 5.5)
        arrow(ax, tx + 0.6, 5.0, tx + 0.6, 4.95, C["db"])

    arrow(ax, 11.9, 5.7, 11.9, 5.5, C["db"], label="call_tool()")
    arrow(ax, 11.9, 5.0, 11.9, 4.95, C["db"])

    # ── OpenAI async ──
    box(ax, 2.7, 6.3, 2.0, 1.0, "AsyncOpenAI\ngpt-4o", "opinions\nrebuttal\nsynthesis", C["external"], 7.5)
    arrow(ax, 5.4, 7.0, 4.7, 6.8, C["external"], label="await")

    # ── LLM Tracker ──
    box(ax, 0.3, 6.3, 2.0, 1.0, "LLM Tracker", "council_mcp_main\ncouncil_rebuttal\ncouncil_synthesis", C["tracker"], 7)
    dashed_arrow(ax, 2.7, 6.8, 2.3, 6.8, C["tracker"], label="track()")

    # ── Streaming SSE back ──
    arrow(ax, 2.7, 4.0, 2.1, 4.0, C["user"], label="SSE stream\nmessages + plan")

    # Nota arquitectura
    ax.text(0.3, 0.5,
            "Protocolo MCP (Model Context Protocol) · Transport SSE preferido en Docker · "
            "stdio como fallback en desarrollo local",
            fontsize=7, color='#475569', style='italic')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — Observabilidad LLM
# ══════════════════════════════════════════════════════════════════════════════
def page_metrics(pdf):
    fig, ax, _ = new_ax(pdf, "5 · Observabilidad LLM — Métricas y Trazabilidad")

    # ── llm_tracker.py ──
    box(ax, 0.3, 5.5, 3.5, 2.8, "llm_tracker.py", "", C["tracker"], 9)
    funcs = [
        "track(user_phone, model, stage,",
        "       response, latency_ms)",
        "",
        "timed_track(user_phone, model,",
        "            stage)  ← context mgr",
        "",
        "_estimate_cost(model, in_tok,",
        "               out_tok, extra)",
    ]
    for i, line in enumerate(funcs):
        ax.text(0.45, 8.0 - i * 0.28, line, fontsize=6.2, color='white',
                family='monospace', zorder=4)

    # ── Tabla de precios ──
    pricing = [
        ("gpt-4o",      "$2.50 / 1M in",  "$10.00 / 1M out"),
        ("gpt-4o-mini", "$0.15 / 1M in",  "$0.60 / 1M out"),
        ("dall-e-3",    "$0.040 / imagen","—"),
        ("whisper-1",   "$0.006 / min",   "—"),
        ("gen3a_turbo", "$0.05 / seg",    "—"),
    ]
    box(ax, 0.3, 3.2, 3.5, 2.1, "Tabla de Precios (PRICING)", "", C["tracker"], 8)
    headers = ["Modelo", "Input / uso", "Output"]
    for j, h in enumerate(headers):
        ax.text(0.5 + j * 1.15, 5.05, h, fontsize=6.5, fontweight='bold',
                color='white', zorder=4)
    for i, (m, inp, out) in enumerate(pricing):
        row_y = 4.75 - i * 0.33
        bg = '#F8F0FF' if i % 2 == 0 else 'white'
        rect = FancyBboxPatch((0.32, row_y - 0.14), 3.46, 0.32,
                              boxstyle="square,pad=0", facecolor=bg, zorder=3)
        ax.add_patch(rect)
        ax.text(0.5,  row_y + 0.02, m,   fontsize=6, color=C["text_dark"], zorder=4)
        ax.text(1.65, row_y + 0.02, inp, fontsize=6, color=C["text_dark"], zorder=4)
        ax.text(2.8,  row_y + 0.02, out, fontsize=6, color=C["text_dark"], zorder=4)

    # ── LLMCall model ──
    box(ax, 0.3, 0.5, 3.5, 2.4, "LLMCall  (db_models.py)", "", C["db"], 8)
    fields = [
        "user_phone  · model  · stage",
        "prompt_tokens  · completion_tokens",
        "total_tokens  · latency_ms",
        "cost_usd  · success",
        "error_message  · created_at",
    ]
    for i, f in enumerate(fields):
        ax.text(0.5, 2.6 - i * 0.33, f"• {f}", fontsize=6.2, color='white',
                family='monospace', zorder=4)

    # Flecha tracker → BD
    arrow(ax, 2.05, 3.2, 2.05, 2.9, C["db"], label="INSERT")

    # ── Stages instrumentados ──
    stages = [
        ("chat_main",             "AgentExecutor"),
        ("chat_tool_followup",    "AgentExecutor"),
        ("video_analyze_image",   "MarketingAgent"),
        ("video_generate_prompt", "MarketingAgent"),
        ("runway_video_generation","MarketingAgent"),
        ("image_classify_intent", "AdminRedactor"),
        ("image_extract_data",    "AdminRedactor"),
        ("council_mcp_main",      "MCPClient"),
        ("council_mcp_followup",  "MCPClient"),
        ("council_opinion",       "CouncilManager"),
        ("council_rebuttal",      "CouncilManager"),
        ("council_synthesis",     "CouncilManager"),
    ]
    box(ax, 4.3, 0.5, 4.8, 7.7, "Stages Instrumentados", "", "#475569", 8)
    ax.text(4.5, 8.0, "Stage", fontsize=7, fontweight='bold', color='white', zorder=4)
    ax.text(7.1, 8.0, "Módulo origen", fontsize=7, fontweight='bold', color='white', zorder=4)
    for i, (stage, origen) in enumerate(stages):
        sy = 7.6 - i * 0.55
        bg = '#F0F4FF' if i % 2 == 0 else 'white'
        rect = FancyBboxPatch((4.32, sy - 0.22), 4.76, 0.48,
                              boxstyle="square,pad=0", facecolor=bg, zorder=3)
        ax.add_patch(rect)
        ax.text(4.5,  sy, stage,  fontsize=6.5, color=C["text_dark"], family='monospace', zorder=4)
        ax.text(7.1,  sy, origen, fontsize=6.5, color='#6366F1', zorder=4)

    arrow(ax, 3.8, 4.0, 4.3, 4.0, C["tracker"], label="track()")

    # ── Dashboard /metrics ──
    box(ax, 9.8, 5.5, 5.8, 2.8, "/metrics  Dashboard", "", C["flask"], 9)
    kpis = [
        ("Coste total estimado (USD)",  "SUM(cost_usd)"),
        ("Tokens totales",              "SUM(total_tokens)"),
        ("Latencia media",              "AVG(latency_ms)"),
        ("Tasa de éxito",               "SUM(success)/COUNT(*)"),
        ("Llamadas por modelo",         "GROUP BY model"),
        ("Coste por modelo",            "GROUP BY model"),
        ("Llamadas por stage",          "GROUP BY stage"),
        ("Histórico 14 días",           "DATE(created_at)"),
    ]
    for i, (kpi, sql) in enumerate(kpis):
        ky = 8.1 - i * 0.32
        ax.text(9.95, ky, f"• {kpi}", fontsize=6.5, color='white', zorder=4)
        ax.text(13.5, ky, sql, fontsize=6, color='#BAE6FD', family='monospace',
                zorder=4, style='italic')

    # Chart.js
    box(ax, 9.8, 3.8, 2.6, 1.4, "Chart.js CDN", "Line · Doughnut\nBar charts", "#0EA5E9", 8)
    box(ax, 12.8, 3.8, 2.8, 1.4, "GET /api/metrics/llm", "JSON endpoint\nAuth required", C["flask"], 8)
    arrow(ax, 11.7, 4.8, 11.7, 5.5, C["flask"], label="fetch()")
    arrow(ax, 12.8, 4.5, 12.6, 4.5, C["flask"])
    arrow(ax, 13.0, 3.8, 13.0, 3.4, C["db"], label="SQL")

    box(ax, 9.8, 0.5, 5.8, 2.8, "Flask-Admin /admin", "Vista tabular LLMCall\nFiltros · Exportar", C["db"], 8)
    arrow(ax, 12.7, 3.8, 12.7, 3.3, C["db"])

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 6 — Flujo completo petición web
# ══════════════════════════════════════════════════════════════════════════════
def page_flow(pdf):
    fig, ax, _ = new_ax(pdf, "6 · Flujo Completo de una Petición Web")

    steps = [
        # (x_center, y_center, label, sublabel, color)
        (1.2,  7.5, "1. Usuario",         "Escribe mensaje\nen PWA (móvil)", C["user"]),
        (3.5,  7.5, "2. HTTPS POST",      "/api/chat\ncon session cookie", C["flask"]),
        (5.8,  7.5, "3. Rate Limiter",    "flask-limiter\n30/min", C["flask"]),
        (8.1,  7.5, "4. Auth Check",      "session['user_phone']\nexiste?", C["flask"]),
        (10.4, 7.5, "5. Load Profile",    "BusinessProfile\nSQLAlchemy", C["db"]),
        (12.7, 7.5, "6. AgentExecutor",   "execute()\nbuild context", C["agent"]),

        (12.7, 5.5, "7. Load History",    "HistoryService\nget_recent(10)", C["db"]),
        (10.4, 5.5, "8. GPT-4o Call",     "chat_main stage\n+ tools schema", C["external"]),
        (8.1,  5.5, "9. Tool Decision",   "tool_calls?\nrouting logic", C["agent"]),

        (5.8,  5.5, "10a. Direct Reply",  "No tools:\nfinal_content", C["flask"]),
        (3.5,  5.5, "10b. Tool Exec",     "CalendarTools /\nAdminRedactor /…", C["agent"]),
        (1.2,  5.5, "10c. Marketing",     "Background thread\nDaemon=True", C["agent"]),

        (1.2,  3.5, "11. GPT Followup",   "chat_tool_followup\nsintetiza resultados", C["external"]),
        (3.5,  3.5, "12. LLM Track",      "track() → LLMCall\ncoste + latencia", C["tracker"]),
        (5.8,  3.5, "13. Save History",   "HistoryService\nsave_interaction()", C["db"]),
        (8.1,  3.5, "14. Notification",   "WebPush / Mail\nsi procede", C["flask"]),
        (10.4, 3.5, "15. JSON Response",  "{'reply': '…'}\n200 OK", C["flask"]),
        (12.7, 3.5, "16. Render PWA",     "JS actualiza\nchat UI", C["user"]),
    ]

    node_w, node_h = 2.0, 1.1

    for cx, cy, label, sub, color in steps:
        box(ax, cx - node_w/2, cy - node_h/2, node_w, node_h, label, sub, color, 7)

    # Flechas fila superior (izq → der)
    top_xs = [1.2, 3.5, 5.8, 8.1, 10.4, 12.7]
    for i in range(len(top_xs) - 1):
        arrow(ax, top_xs[i] + node_w/2, 7.5, top_xs[i+1] - node_w/2, 7.5, C["arrow"])

    # Bajada de 12.7 a 12.7
    arrow(ax, 12.7, 7.5 - node_h/2, 12.7, 5.5 + node_h/2, C["arrow"])

    # Fila media (der → izq)
    mid_xs = [12.7, 10.4, 8.1, 5.8, 3.5, 1.2]
    for i in range(len(mid_xs) - 1):
        arrow(ax, mid_xs[i] - node_w/2, 5.5, mid_xs[i+1] + node_w/2, 5.5, C["arrow"])

    # Bajada de 1.2 a 1.2
    arrow(ax, 1.2, 5.5 - node_h/2, 1.2, 3.5 + node_h/2, C["arrow"])

    # Fila inferior (izq → der)
    bot_xs = [1.2, 3.5, 5.8, 8.1, 10.4, 12.7]
    for i in range(len(bot_xs) - 1):
        arrow(ax, bot_xs[i] + node_w/2, 3.5, bot_xs[i+1] - node_w/2, 3.5, C["arrow"])

    # ── Tiempos ──
    ax.text(0.3, 2.2, "Tiempos típicos:", fontsize=8, fontweight='bold', color=C["text_dark"])
    timings = [
        ("Auth + BD load",         "< 5 ms"),
        ("GPT-4o (chat_main)",     "600 – 1500 ms"),
        ("GPT-4o (tool followup)", "400 – 900 ms"),
        ("Runway video gen",       "20 – 90 s  (background)"),
        ("AdminRedactor PDF",      "1 – 3 s"),
        ("Total (sin vídeo)",      "1 – 3 s"),
    ]
    for i, (desc, t) in enumerate(timings):
        ax.text(0.3 + (i % 3) * 5.2, 1.8 - (i // 3) * 0.45,
                f"{desc}: {t}", fontsize=7, color=C["text_dark"])

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
with PdfPages(OUT) as pdf:
    # Portada
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor(C["header"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.set_facecolor(C["header"])
    title_page(ax,
               "Ticketia / Zeptai\nArquitectura del Sistema",
               "Asistente IA para Autónomos y PYMEs · Agentes Proactivos · MCP · LLM Observability")
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

    page_overview(pdf)
    page_db(pdf)
    page_agents(pdf)
    page_mcp(pdf)
    page_metrics(pdf)
    page_flow(pdf)

print(f"PDF generado: {OUT}")
