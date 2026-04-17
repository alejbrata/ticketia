# 🎓 Guía de Ejecución para Defensa TFM

Sigue estos pasos para levantar el entorno completo de Ticketia (Zeptai) durante la demostración en vivo.

## 1. Terminal Principal: La Aplicación Web
Esta terminal levanta el servidor Flask, la interfaz web y los agentes inteligentes (incluido "El Consejo").

```powershell
# Desde la carpeta raíz del proyecto
cd TICKETIA_PRO
python app.py
```

*   **Estado**: Esperar a ver `Running on http://0.0.0.0:5000`.
*   **Acceso**: Abre [http://localhost:5000](http://localhost:5000) en tu navegador.

## 2. Terminal Secundaria: El Scheduler (Opcional)
Esta terminal ejecuta los procesos en segundo plano, como el **Business Coach** que analiza las finanzas diariamente.

```powershell
# Abre una SEGUNDA terminal
cd TICKETIA_PRO
python run_scheduler.py
```

*   **Estado**: Verás un mensaje `🚀 Scheduler Activo`.
*   **Nota**: Si no lo lanzas, la web funciona igual, pero no habrá notificaciones *push* proactivas simuladas en segundo plano.

## 3. Despliegue Rápido con Docker (Para Evaluadores)
Si prefieres no instalar dependencias de Python localmente, puedes levantar todo el ecosistema (Web + Scheduler) con Docker Compose:

```powershell
# Asegúrate de tener Docker Desktop iniciado
docker-compose up --build
```
*   **Estado**: La app estará disponible en [http://localhost:5000](http://localhost:5000).
*   **Detener**: Pulsa `Ctrl+C` o ejecuta `docker-compose down`.

## 4. Credenciales y Datos Demo
Si necesitas loguearte durante la demo:
*   **Teléfono**: El que has configurado en `seed_owner.py` (ej: `+34600...`).
*   **Resetear Datos**: Si quieres empezar de cero antes del tribunal:
    ```powershell
    python reset_db_full.py
    ```
    *(¡Cuidado! Borra todo y crea un usuario limpio).*

## 5. Cargar la Base de Conocimiento (RAG con pgvector)

Antes de la demo, sube el PDF de la empresa para que el asistente pueda responder con datos reales.

**Archivo listo para usar**: `ialex_solutions_knowledge_base.pdf` (raíz del repo)

**Pasos**:
1.  Entra en la app y ve a **Menú lateral → 📚 Base de Conocimiento** (o accede directamente a [http://localhost:5000/knowledge](http://localhost:5000/knowledge)).
2.  Arrastra el archivo `ialex_solutions_knowledge_base.pdf` sobre la zona de subida o pulsa para seleccionarlo.
3.  Pulsa **"Procesar e indexar"** — la app lo trocea en fragmentos de ~400 caracteres y genera los embeddings con `text-embedding-3-small` en segundo plano.
4.  Cuando aparezca el documento en la lista de "Documentos indexados", el RAG está activo.

**Verificar que funciona** — prueba estas preguntas en el chat:
*   `"¿Cuánto cuesta implantar un agente IA?"` → debe responder con las tarifas del catálogo
*   `"¿Tenéis demo gratuita?"` → debe mencionar la demo de 45 minutos en hola@ialex-solutions.com
*   `"¿Qué modelos de IA usáis?"` → debe listar GPT-4o, Claude 3.5, Gemini 1.5 Pro

> **Cómo funciona por dentro**: cada fragmento se convierte en un vector de 1.536 dimensiones almacenado en PostgreSQL con la extensión `pgvector`. Al llegar una pregunta, se buscan los 5 fragmentos más similares por distancia coseno y se inyectan en el contexto del LLM antes de generar la respuesta.

---

## 6. Guion Rápido de Demo (Checklist)
1.  **Login/Dashboard**: Mostrar KPIs y gráfica de gastos.
2.  **Subir Ticket**: Usar el botón de la cámara (simulado) y ver cómo la IA extrae el dato.
3.  **RAG en acción**: Ir al chat y preguntar sobre tarifas o servicios de IAlex Solutions — el agente responde con datos del PDF indexado.
4.  **El Consejo (WOW)**: Ir a "Sala de Juntas", lanzar una pregunta estratégica y dejar que debatan.
5.  **Generar Documento**: Pedir al bot que genere un PDF o Excel.
6.  **Demostración MCP (Extra)**: Explicar cómo los agentes ahora son Locales-Primero. Mostrar el servidor `mcp_server_sse.py` u Open una nueva terminal y lanzar `python test_council_async.py` para demostrar cómo el agente busca en internet el BOE en tiempo real.
