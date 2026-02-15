# Guía Maestra de Defensa TFM: Arquitectura Ticketia AI

Este documento es tu "Biblia" para la defensa. Contiene el nivel de detalle necesario para responder a cualquier pregunta técnica del tribunal, desde la arquitectura general hasta la línea de código específica.

---

## 🏗️ Capítulo 1: Arquitectura General y Stack Tecnológico

### ¿Por qué esta arquitectura?
Hemos elegido una arquitectura **Monolito Modular** basada en **Python**.
*   **Python**: Lenguaje nativo de la IA. Facilita la integración con OpenAI, Pandas (análisis de datos) y PyTorch (si se necesitara). Usar Java aquí habría añadido complejidad innecesaria (JNI/puentes) para hablar con los modelos.
*   **Flask**: Framework web minimalista (Microframework). A diferencia de Django o Spring Boot, Flask nos da control total sobre el ciclo de vida de la petición, lo cual es crítico cuando manejamos conexiones Websocket o Long-Polling para IA.
*   **SQLAlchemy (ORM)**: Abstracción de base de datos. Nos permite desarrollar en SQLite (fichero) y desplegar en PostgreSQL sin cambiar una sola línea de lógica.

### Diagrama Mental de Flujo
1.  **Usuario** interactúa (Web o WhatsApp).
2.  **Flask (`app.py`)** recibe la petición HTTP.
3.  **Manager (`manager.py`)** toma el control si es una tarea de IA.
4.  **LLM (GPT-4o)** "piensa" y decide qué herramienta usar.
5.  **Tools (`tools.py` / `logic.py`)** ejecutan la acción (Guardar en DB, consultar API externa).
6.  **Respuesta** se genera y se envía al usuario.

---

## 🧠 Capítulo 2: El Cerebro Agéntico (`modules/agents/`)

Esta es la joya de la corona. No es un chatbot simple de "pregunta-respuesta", es un **Agente Orquestador**.

### El Orquestador (`manager.py`)
Este archivo implementa el bucle de razonamiento (Reasoning Loop).
*   **Concepto Clave**: *ReAct (Reason + Act)*.
*   **Cómo funciona el código**:
    1.  Recibe el mensaje del usuario.
    2.  Inyecta el **System Prompt** (personalidad y reglas de negocio del `BusinessProfile`).
    3.  Envía el mensaje + la lista de herramientas (`TOOLS_SCHEMA`) a la API de OpenAI.
    4.  **Paso Crítico**: OpenAI no ejecuta la herramienta. OpenAI devuelve un JSON diciendo: *"Por favor, ejecuta la función `check_availability` con fecha '2023-10-20'"*.
    5.  El `run_agent` detecta esta petición (`tool_calls`), busca la función Python real en `tools.py`, la ejecuta, y le devuelve el resultado a la IA.
    6.  La IA genera la respuesta final en lenguaje natural con ese dato.

### Las Herramientas (`tools.py`)
Aquí definimos las "manos" del agente.
*   **Clase `CalendarTools`**:
    *   `check_availability`: Consulta la tabla `Appointment` en la BD.
    *   **Lógica**: Filtra citas existentes y calcula huecos libres restando de una lista fija (`all_slots`).
*   **Schema (`TOOLS_SCHEMA`)**: Es la "API" que le enseñamos al LLM. Define qué puede hacer y qué parámetros necesita.

---

## 🧾 Capítulo 3: Módulo de Tickets (`modules/tickets/logic.py`)

Este módulo demuestra la capacidad de **Multimodalidad** (Visión + Texto).

### Pipeline de Procesamiento (`process_ticket`)
1.  **Ingesta**: Recibe una URL de imagen (de Twilio/WhatsApp) o un archivo local (Web).
2.  **Normalización**: Descarga la imagen y la convierte a **Base64**. Esto es necesario porque las APIs de LLM actuales (GPT-4o Vision) requieren la imagen encolada en el JSON de la petición.
3.  **Extracción Cognitiva (OCR Inteligente)**:
    *   No usamos un OCR tradicional (Tesseract) que falla con arrugas o mala luz.
    *   Usamos **GPT-4o Vision** con un prompt específico ("Actúa como experto contable...").
    *   Le pedimos **JSON Estricto**. Esto es vital para poder guardar los datos estructurados en la BD.
4.  **Persistencia**:
    *   Creamos un objeto `Ticket` (Modelo definido en `db_models.py`).
    *   Guardamos tanto los datos estructurados (`total`, `fecha`) como el JSON crudo (`raw_data`) por si acaso necesitamos re-procesar en el futuro.

---

## 🚀 Capítulo 4: Sistemas Proactivos (`modules/proactive/`)

Aquí es donde el sistema deja de ser reactivo y pasa a trabajar solo.

### Cazador de Ayudas (`grant_hunter.py`)
**Problema**: Buscar subvenciones es aburrido y costoso (tokens) si leemos 1000 BOEs diarios.
**Solución**: Arquitectura de Filtrado en Embudo.
1.  **Nivel 1 (SQL - Coste 0)**: Filtramos por palabras clave obvias en la base de datos. Si el usuario es "Panadero", ignoramos ayudas del sector "Automoción".
2.  **Nivel 2 (IA Ligera - GPT-4o-mini)**: Para los casos dudosos, usamos un modelo pequeño y barato para desambiguar.
    *   *Pregunta*: "¿La ayuda 'Digital Kit' aplica a una panadería?" -> *Respuesta*: SI/NO.
3.  **Nivel 3 (IA Potente - GPT-4o)**: Solo si pasa los filtros, usamos el modelo caro para redactar el mensaje de WhatsApp persuasivo ("¡Pepe, mira esto!").

### Agente de Marketing (`marketing_agent.py`)
**Reto**: Generar un vídeo tarda minutos. No podemos dejar al usuario esperando en el navegador 5 minutos (Timeout HTTP).
**Solución**: **Ejecución Asíncrona (Background Workers)**.
*   El usuario pide "Vídeo de zapatos".
*   El sistema lanza un **Hilo (Threading)** y responde inmediatamente al usuario: "¡Oído! Me pongo a ello, te avisaré cuando esté".
*   En segundo plano (`_async_marketing_worker`):
    1.  Analiza la imagen de los zapatos (Vision).
    2.  Genera un prompt de animación.
    3.  Llama a la API de **RunwayML** (SOTA en vídeo generativo).
    4.  Hace **Polling** (pregunta cada 30 segs) hasta que el vídeo está listo.
    5.  Cuando termina, guarda el archivo y envía una notificación.

---

## 🛡️ Capítulo 5: MLOps y Calidad (`mlops/`)

¿Cómo sabemos que el sistema funciona?

### LLM-as-a-Judge (`eval_agents.py`)
Implementamos un marco de evaluación automática.
*   `gold_standard.json`: Nuestra "hoja de respuestas correctas".
    *   *Input*: "Quiero hora para mañana".
    *   *Expected*: Intent `BOOKING`, Tool `check_availability`.
*   **El Juez**: Usamos GPT-4o para corregir a GPT-4o. Si la respuesta del agente no coincide con la intención esperada, el juez suspende el test.
*   **CI/CD**: Integrado en GitHub Actions. No se puede subir código a producción si la "inteligencia" del agente baja del 70%.

---

## ⚔️ Argumentario de Defensa (Preguntas Trampa)

### P: "¿Por qué no usasteis LangChain?"
**R**: "Analizamos LangChain, pero añade una capa de abstracción muy gruesa que dificulta el depurado (debugging) y oculta los prompts reales. Para un sistema empresarial crítico, preferimos controlar directamente las llamadas a la API (OpenAI SDK) para tener control total sobre la latencia, el coste y el manejo de errores, implementando solo los patrones que realmente necesitamos."

### P: "¿Es escalable usar SQLite?"
**R**: "Para el prototipo y la defensa, SQLite es perfecto por su portabilidad. Sin embargo, el uso de **SQLAlchemy** como ORM desacopla nuestra lógica de la base de datos. Cambiar a PostgreSQL para manejar millones de usuarios es literalmente cambiar una línea de configuración (`SQLALCHEMY_DATABASE_URI`) en producción, sin tocar el código de los agentes."

### P: "¿Cómo manejáis la privacidad de las facturas?"
**R**: "Aplicamos el principio de **mínima exposición**. Las imágenes de las facturas se procesan para extraer datos y se descartan del contexto de la IA inmediatamente. No usamos los datos de los usuarios para re-entrenar modelos públicos (política 'Zero Data Retention' de la API Enterprise de OpenAI)."

### P: "¿Qué pasa si GPT 'alucina' un precio?"
**R**: "Por eso implementamos el campo `raw_data` y mantenemos la imagen original. Además, en la interfaz de usuario, siempre mostramos los datos extraídos para que el humano valide antes de contabilizar. La IA es un copiloto, no el piloto automático definitivo en temas fiscales."
