# Zeptai — Plataforma de IA para Pymes

> Trabajo de Fin de Máster · IA Generativa aplicada a la gestión de pequeñas y medianas empresas

---

## Resumen

**Zeptai** es una PWA (Progressive Web App) que combina múltiples modelos de IA (GPT-4o, Whisper, Runway Gen-3) para automatizar la gestión diaria de una pyme: digitalización de gastos, búsqueda de subvenciones, análisis financiero proactivo, generación de contenido y atención al cliente.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE (PWA)                        │
│          HTML + Tailwind CSS · Service Worker · Push        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────────┐
│                   FLASK (Gunicorn sync)                     │
│   routes/web.py    routes/api.py    mcp_server_sse.py       │
└──────┬────────────┬──────────────┬──────────────────────────┘
       │            │              │
┌──────▼──────┐ ┌───▼────────┐ ┌──▼───────────────────────┐
│  Módulos IA │ │  SQLAlchemy│ │  MCP Server (FastMCP SSE) │
│             │ │  PostgreSQL│ │  tools: stats, email, etc  │
│ • chatbot   │ └────────────┘ └──────────────────────────┘
│ • agents    │
│   - grant_hunter        ← APScheduler (09:00 diario)
│   - business_health     ← APScheduler (09:00 diario)
│   - networker           ← APScheduler (09:00 diario)
│   - post_sales
│   - admin_redactor
│   - marketing_agent     ← Runway Gen-3 Alpha
│ • council (multi-agent) ← SSE streaming
└─────────────┘

APIs Externas:
  OpenAI  → GPT-4o (chat, vision, análisis)
          → Whisper (transcripción de voz)
  Runway  → Gen-3 Alpha (generación de vídeo)
  Twilio  → WhatsApp Business (opcional)
```

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.10 · Flask · SQLAlchemy · Gunicorn |
| Base de datos | PostgreSQL (prod) · SQLite (test) |
| IA | OpenAI GPT-4o · Whisper · Runway Gen-3 |
| Frontend | HTML5 · Tailwind CSS · PWA (manifest + SW) |
| Tareas programadas | APScheduler |
| Herramientas IA | FastMCP (Model Context Protocol) |
| CI/CD | GitHub Actions (`.github/workflows/mlops.yml`) |
| Contenedores | Docker · Docker Compose |

---

## Módulos principales

### Agentes proactivos (background)
- **`business_health.py`** — Analiza gastos diarios, proyecta fin de mes, alerta si hay desviación >20%
- **`grant_hunter.py`** — Escanea subvenciones (BOE/CDTI/Kit Digital), filtra por sector con GPT-4o
- **`networker.py`** — Detecta sinergias entre usuarios de la plataforma
- **`post_sales.py`** — Detecta quejas e incidencias en mensajes de clientes

### Módulo Council (multi-agente)
3 agentes debaten en tiempo real via SSE streaming:
- **El Socio** (🐯) — perspectiva comercial y ventas
- **El Gestor** (🦉) — perspectiva fiscal y legal
- **El Coach** (🚀) — estrategia y productividad

### MLOps
- `mlops/eval_agents.py` — evaluaciones de calidad sin llamadas reales a la API
- Workflow CI/CD en GitHub Actions: tests unitarios + evaluaciones en cada push

---

## Instalación local

### Requisitos
- Docker Desktop instalado y en ejecución
- API key de OpenAI con acceso a GPT-4o

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/alejbrata/ticketia.git
cd ticketia

# 2. Configurar variables de entorno
cp .env.example .env
```

Abre `.env` y rellena al menos estas dos variables:
```
SECRET_KEY=<cadena aleatoria larga>
OPENAI_API_KEY=sk-...
```
Las demás son opcionales para la evaluación básica (ver tabla abajo).

```bash
# 3. Levantar la aplicación con Docker
docker compose up -d

# 4. Cargar todos los datos demo de una vez
docker compose exec web python seed_all.py

# 5. Abrir en el navegador
# http://localhost:5000
# Usuario: admin@demo.com  |  Contraseña: demo1234
```

`seed_all.py` hace en un solo paso: reset de BD, usuario demo con plan PRO_FULL, configuración del asistente IA (sector, FAQ, garantías), generación e indexación del PDF de conocimiento en pgvector (25 chunks RAG) y 15 tickets de historial de gastos.

Para volver a empezar de cero en cualquier momento:

```bash
docker compose exec web python seed_all.py
```

### Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|:-----------:|-------------|
| `SECRET_KEY` | Sí | Clave Flask — genera con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENAI_API_KEY` | Sí | API key de OpenAI ([platform.openai.com/api-keys](https://platform.openai.com/api-keys)) |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | No | Gmail + App Password para envío de correos |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | No | Push notifications PWA (genera con `npx web-push generate-vapid-keys`) |
| `RUNWAYML_API_SECRET` | No | Generación de vídeo con Runway Gen-3 |
| `DATABASE_URL` | No | PostgreSQL externo — Docker Compose usa SQLite por defecto |

---

## Tests

```bash
# Desde el directorio raíz
cd TICKETIA_PRO
python -m unittest discover tests
```

Los tests usan SQLite en memoria y mocks de OpenAI para ejecutarse sin coste ni red.

**Cobertura:** 143 tests — autenticación, agentes proactivos, MCP tools, métricas LLM, admin redactor.

---

## Pipeline CI/CD

El workflow `.github/workflows/mlops.yml` se ejecuta en cada push a `main`, `dev` y `feature/*`:

1. **Install dependencies** — `pip install -r requirements.txt`
2. **Unit tests** — `python -m unittest discover tests`
3. **Agent evaluations** — `python mlops/eval_agents.py`

---

## Demo (presentación TFM)

Accede a `/demo` una vez logueado para el panel guiado de la presentación:

1. **Preparar datos** — inyecta historial de gastos y subvenciones BOE
2. **Business Coach** — analiza gastos y genera alerta financiera en vivo
3. **Grant Hunter** — escanea subvenciones compatibles con el sector

Las notificaciones generadas aparecen en tiempo real en el Dashboard.

---

## Autor

**Alejandro Bratasanu** — TFM Máster en IA Generativa · 2026
