# 🔌 Guía de Pruebas: Integración MCP (Model Context Protocol) en Ticketia

Esta guía detalla cómo probar la integración bidireccional del **Model Context Protocol (MCP)** en Ticketia. Hemos dotado a Ticketia de "superpoderes", permitiendo que funcione tanto como un **Servidor MCP** (exponiendo datos a IAs externas) como un **Cliente MCP** (permitiendo a los agentes internos usar herramientas reales).

---

## 1. Ticketia como un Servidor MCP (SSE) 📤

Hemos convertido la base de datos de Ticketia en una fuente de información estandarizada para IAs externas (como la aplicación de escritorio de Claude).

*   **¿Qué hace?** Levanta un servidor web en el puerto 8000 que se comunica usando *Server-Sent Events (SSE)*.
*   **La Herramienta:** Expone `get_financial_summary`. Si una IA provee un número de teléfono, Ticketia devolverá un resumen de los gastos de ese mes de forma segura.

### Pasos para probarlo:

Esta prueba simula ser una aplicación externa preguntándole a Ticketia por los gastos de un usuario.

1.  Abre una terminal en la carpeta raíz del proyecto (`TICKETIA_PRO`).
2.  Inicia el servidor SSE ejecutando:
    ```bash
    python mcp_server_sse.py
    ```
    *El servidor arrancará en `http://127.0.0.1:8000/sse`.*
3.  **No cierres esta terminal**. Abre una SEGUNDA terminal en la misma carpeta.
4.  En la segunda terminal, ejecuta el cliente de prueba:
    ```bash
    python test_mcp_sse_client.py
    ```
5.  **Resultado esperado:** El script se conectará por HTTP, descubrirá la herramienta `get_financial_summary`, la ejecutará y la consola imprimirá un mensaje real extraído de la base de datos de Ticketia ("No se han encontrado tickets..." o el listado de gastos real).

---

## 2. Ticketia como un Cliente MCP (El "Cerebro" de los Agentes) 🧠

Hemos conectado a los agentes internos de Ticketia (por ejemplo, "El Consejo" o "El Gestor") a herramientas del mundo real para que las usen *antes* de responder al usuario.

*   **Las Herramientas Creadas**:
    1.  **`search_web`**: Usa DuckDuckGo para buscar en internet en tiempo real (ideal para buscar ayudas del BOE).
    2.  **`schedule_appointment`**: Se conecta con la base de datos (`Appointment`) para crear citas reales.
    3.  **`send_email_notification`**: Usa Flask-Mail para enviar correos electrónicos de forma autónoma.
*   **Cómo funciona:** El Orquestador (`modules/council/orchestrator.py`) ahora es asíncrono. Cuando un agente necesita información externa, pausa su respuesta, utiliza el cliente MCP (`core/mcp_client.py`) para ejecutar una herramienta local, recibe el resultado y luego construye una opinión final fundamentada.

### Pasos para probarlo:

Esta prueba ejecuta a tu agente "El Gestor" y le pide que busque información actualizada en internet utilizando la herramienta recién creada.

1.  Abre una terminal en la carpeta raíz (`TICKETIA_PRO`).
2.  Ejecuta el entorno de prueba del Consejo Asíncrono:
    ```bash
    python test_council_async.py
    ```
3.  **Resultado esperado:**
    *   Verás inicializarse la sesión del Consejo con un dilema simulado: *"Quiero saber si hay ayudas vigentes en el BOE para reformistas en Madrid."*
    *   En la consola aparecerá el mensaje: `🔧 Agent requested tool: search_web`. ¡Este es el agente decidiendo usar la herramienta de búsqueda de forma autónoma!
    *   Tras unos segundos buscando en la web en segundo plano, "El Gestor" responderá basándose en lo que ha leído en internet (incluyendo resúmenes y enlaces reales).
    *   Finalmente, el Secretario del Consejo sintetizará un plan de acción basado en esta información obtenida en tiempo real del exterior.
