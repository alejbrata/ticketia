# -*- coding: utf-8 -*-
preguntas = """# 100 Preguntas del Tribunal TFM — Ticketia Pro / Zeptai

---

## CATEGORIA 1: VISION GENERAL Y MOTIVACION (1-15)

**1. Por que elegiste las PYMEs como target?**
Las grandes empresas tienen soluciones enterprise consolidadas (Salesforce, SAP). Las PYMEs carecen de recursos para implementarlas y suponen el 99,8% del tejido empresarial espanol. El gap tecnologico es mayor y la propuesta de valor mas clara.

**2. Que problema concreto resuelve Ticketia Pro que no resuelva ChatGPT directamente?**
ChatGPT es generico. Ticketia esta integrado con la BD del negocio (citas reales, documentos propios), tiene agentes proactivos autonomos, genera PDFs profesionales y envia notificaciones push. No requiere conocimientos tecnicos del usuario.

**3. Cual es el diferenciador principal respecto a Tidio o Intercom?**
Esos son chatbots reactivos de atencion al cliente. Ticketia Pro es un asistente de gestion empresarial multimodal: agenda citas, genera documentos, crea material de marketing y debate estrategias. El scope es radicalmente distinto.

**4. Por que SaaS y no solucion on-premise?**
SaaS permite actualizaciones continuas, no requiere infraestructura del cliente, facilita el modelo de suscripcion recurrente y reduce el coste de soporte. Para PYMEs sin departamento IT es la unica opcion viable.

**5. Cual es el modelo de negocio exacto?**
Suscripcion mensual por tiers: BASIC (chatbot + agenda, 49 EUR/mes), PRO (+ marketing + consejo pyme, 99 EUR), ENTERPRISE (+ agentes proactivos + MCP, 199 EUR). Margen bruto estimado del 85%, tipico de SaaS.

**6. Como gestionas el onboarding de un nuevo negocio?**
Mediante el Wizard multi-step (/wizard): el usuario configura nombre, sector, horario, servicios y tono del bot, y sube documentos al RAG. El agente queda personalizado sin escribir una sola linea de codigo.

**7. Que riesgo principal identificas en el modelo de negocio?**
Dependencia de la API de OpenAI (riesgo de cambios de precio o politica). Mitigacion: la arquitectura abstrae el cliente LLM con get_openai_client(), permitiendo cambiar de proveedor con cambios minimos.

**8. Por que PWA y no app nativa iOS/Android?**
Cero coste de distribucion (no requiere App Store), instalable desde el navegador, misma base de codigo y soporte de Web Push para notificaciones. Para el MVP es la decision mas eficiente.

**9. Cual es el break-even del proyecto?**
Con infraestructura de 50 EUR/mes y coste OpenAI de 5 EUR/usuario/mes, el break-even esta en aproximadamente 3 clientes PRO (99 EUR/mes). A partir de 10 clientes el margen supera el 70%.

**10. Que harías diferente si empezaras desde cero?**
Usaria FastAPI+async desde el inicio, Celery+Redis en lugar de threading, y migraciones Alembic en lugar de create_all(). Tambien separaria el identificador de usuario del numero de telefono desde el principio.

**11. Por que no usas LangChain o LlamaIndex para el RAG?**
Anaden abstraccion que oculta lo que ocurre internamente. Implementar RAG desde cero con pgvector permite entender y justificar cada decision tecnica. En produccion real, LlamaIndex podria acelerar el desarrollo.

**12. Como garantizas que el agente no alucina datos de la empresa?**
El RAG inyecta unicamente informacion indexada por el propio negocio. El system prompt instruye: "Si la respuesta no esta en el contexto, indicalo." GPT-4o es conservador cuando no tiene contexto suficiente.

**13. Que limitacion legal tiene usar GPT-4o para procesar datos de clientes?**
Los datos se envian a la API de OpenAI. Para uso empresarial en Europa se necesita un DPA (Data Processing Agreement) firmado con OpenAI y clausulas especificas en el contrato con el cliente final (RGPD).

**14. Cuantos usuarios concurrentes puede manejar el sistema actual?**
Con 2 workers Gunicorn+gevent, cientos de conexiones simultaneas para requests rapidas. El cuello de botella real es el rate limit de OpenAI (3500 RPM en tier 1), no la infraestructura propia.

**15. Por que elegiste Python como lenguaje principal?**
Ecosistema de IA mas maduro (OpenAI SDK, pgvector, pymupdf4llm, pptx), rapidez de prototipado y dominio previo. Para produccion a escala, Go ofreceria mejor rendimiento pero a costa de velocidad de desarrollo.

---

## CATEGORIA 2: ARQUITECTURA TECNICA (16-35)

**16. Que es exactamente el patron AgentExecutor?**
Un orquestador stateless que recibe un mensaje, construye el contexto (RAG + historial), lanza la primera llamada LLM, ejecuta tools si las hay, y lanza la segunda llamada para sintetizar. Se instancia por request HTTP y no mantiene estado entre llamadas.

**17. Por que stateless? Ventajas e inconvenientes.**
Ventajas: escalabilidad horizontal trivial, sin estado compartido entre workers, sin race conditions. Inconvenientes: el contexto debe reconstruirse en cada request con queries a BD, sin cache en memoria entre turnos.

**18. Como funciona el patron de dos llamadas al LLM?**
Primera llamada: el LLM decide si responder directamente o ejecutar una tool (finish_reason="tool_calls"). Segunda llamada: si hubo tools, se anaden los resultados al historial y se llama de nuevo al LLM sin tools, forzando una respuesta en lenguaje natural.

**19. Que pasa si el LLM encadena multiples tools en una sola respuesta?**
_process_tool_calls() itera sobre response_message.tool_calls (que puede contener N tool calls). Todas se ejecutan secuencialmente y sus resultados se anaden al historial antes de la segunda llamada LLM.

**20. Como manejas errores en la ejecucion de tools?**
Cada tool tiene try/except interno que devuelve un string de error descriptivo. El LLM recibe ese string como resultado y lo comunica al usuario en lenguaje natural. Hay ademas un try/except global en execute() para errores inesperados.

**21. Por que gevent en Gunicorn?**
Gunicorn con worker class gevent usa coroutines para manejar multiples requests concurrentes sin bloquear el GIL durante operaciones I/O (llamadas HTTP a OpenAI). Sin gevent, 2 workers solo manejan 2 requests simultaneas; con gevent, cada worker maneja cientos.

**22. Como funciona el entrypoint.sh y por que es importante?**
Ejecuta db.create_all() UNA vez antes de lanzar Gunicorn. Sin esto, si 2 workers arrancan simultaneamente ambos intentarian crear las tablas a la vez, causando race conditions en el schema de la BD.

**23. Por que Docker Compose con 4 servicios y no un monolito?**
No es microservicios estrictos, es un monolito modular con servicios auxiliares. El scheduler y el MCP son procesos independientes por necesidad (ciclo de vida distinto), no por dogma arquitectonico. Flask sigue siendo el nucleo.

**24. Como se comunican los 4 servicios Docker entre si?**
Por red interna Docker (ticketia_network). Los nombres de servicio actuan como hostnames: DATABASE_URL=postgresql://postgres@db:5432/ticketia_db, MCP_SSE_URL=http://mcp:8001/sse.

**25. Cual es el timeout maximo de una request al agente?**
Gunicorn tiene --timeout 300 (5 minutos). En la practica: GPT-4o tarda 2-10s, PDF ~1s, DALL-E ~10s. El unico caso que supera 30s es la generacion de video (Runway), que se ejecuta en background thread.

**26. Como funciona el background thread del marketing?**
run_marketing_thread() lanza un Thread(target=...).start() que ejecuta la generacion de imagen/PPT/video mientras el HTTP handler devuelve inmediatamente una respuesta al usuario. Al terminar, el thread envia una notificacion in-app.

**27. Que riesgo tiene usar threads de Python en lugar de Celery?**
Los threads comparten el proceso Flask. Si el proceso se reinicia, los jobs en vuelo se pierden sin posibilidad de recovery. Celery+Redis persiste los jobs y permite reintentos automaticos. Es la deuda tecnica mas critica del sistema.

**28. Como funciona el rate limiter?**
Flask-Limiter aplica limites por IP: 30 requests/minuto en /api/chat, 20 requests/hora en /upload_web_audio. El almacenamiento es en memoria (por defecto), lo que significa que los contadores se resetean al reiniciar el servidor.

**29. Como gestionas las migraciones de schema de BD?**
Actualmente con db.create_all() en el entrypoint, que crea tablas si no existen pero no gestiona cambios de schema. En produccion se necesitaria Alembic para migraciones incrementales sin perder datos.

**30. Por que SQLite en desarrollo y PostgreSQL en produccion?**
SQLite no requiere servidor, ideal para desarrollo local rapido. PostgreSQL es necesario en produccion por pgvector (extension no disponible en SQLite), robustez transaccional y soporte de concurrencia real.

**31. Como abstraes el cliente de OpenAI?**
A traves de core/clients.py con get_openai_client() que retorna una instancia configurada. Esto permite cambiar de proveedor (Azure OpenAI, Mistral) modificando solo ese fichero, sin tocar el codigo del agente.

**32. Que es el LLMTracker y como funciona?**
Modulo que registra automaticamente cada llamada a modelos de IA: modelo, stage, tokens entrada/salida, latencia en ms, coste estimado y exito. Los datos se persisten en la tabla LLMCall y se visualizan en /metrics con Chart.js.

**33. Como calculas el coste estimado de cada llamada LLM?**
Mediante una tabla PRICING en llm_tracker.py con el precio por millon de tokens de cada modelo (ej: gpt-4o: 2,50 USD input, 10,00 USD output). Se calcula: (prompt_tokens/1M * precio_input) + (completion_tokens/1M * precio_output).

**34. Como manejas la sesion del usuario entre requests?**
Flask session con cookie firmada (SECRET_KEY). El user_phone se almacena en session['user_phone'] tras el login. Como el agente es stateless, reconstruye el contexto en cada request leyendo la BD con ese identificador.

**35. Por que no usas JWT en lugar de sesiones Flask?**
Flask session es suficiente para una aplicacion web tradicional con renderizado server-side. JWT seria mas apropiado si hubiera una API REST consumida por clientes moviles nativos o SPAs. Para el MVP, session es mas simple y seguro out-of-the-box.

---

## CATEGORIA 3: AGENTE IA Y TOOL CALLING (36-55)

**36. Que es el Tool Calling de OpenAI y como lo usas?**
Es un mecanismo por el que el desarrollador define schemas JSON de funciones disponibles. El LLM decide cuando llamarlas y con que argumentos. El desarrollador ejecuta la funcion real y devuelve el resultado al LLM para que sintetice la respuesta final.

**37. Cuantas tools tiene el agente y cuales son?**
Seis tools: check_availability (consulta huecos en agenda), book_appointment (reserva cita), create_proposal_from_last_image (presupuesto PDF desde imagen), create_proposal_from_text (presupuesto desde texto/voz), generate_marketing_material (imagen/PPT/video), handle_customer_service (gestion postventa).

**38. Como anadirias una nueva tool sin romper el sistema?**
Tres pasos: (1) definir el schema JSON en TOOLS_SCHEMA, (2) implementar la funcion Python, (3) anadir un elif en _process_tool_calls(). El LLM aprende a usarla solo por la descripcion del schema, sin reentrenamiento ni cambios en el orquestador.

**39. Por que book_appointment tiene client_name y phone como opcionales?**
Porque forzar al usuario a dar su nombre y telefono para agendar una cita es friccion innecesaria. El schema original los tenia como required, lo que hacia que el agente los pidiera siempre. Al hacerlos opcionales el agente solo los solicita si el usuario los menciona.

**40. Como sabe el agente la fecha de hoy para interpretar "el viernes"?**
_build_rag_system_prompt() inyecta datetime.now().strftime("%A, %d de %B de %Y") en el system prompt en cada request. Sin esto, el modelo usaria su fecha de corte de entrenamiento y calcularia fechas incorrectas.

**41. Que pasaria si el LLM inventa argumentos para una tool que no tiene?**
_process_tool_calls() tiene un bloque else final que devuelve "Error: Herramienta desconocida." al LLM. Esto es raro en la practica porque GPT-4o respeta el schema definido en TOOLS_SCHEMA.

**42. Como verificas que no se reserven dos citas en el mismo horario?**
CalendarTools.book_appointment() hace una query filter_by(business_phone, date, time) antes del INSERT. Si existe conflicto, devuelve error string. La verificacion es dentro de la misma sesion SQLAlchemy, pero en produccion se necesitaria un lock de BD para evitar race conditions bajo alta concurrencia.

**43. Que es el system prompt y como se construye en cada request?**
Es el mensaje de rol "system" que da contexto e instrucciones al LLM. Se construye dinamicamente en _build_rag_system_prompt(): prompt base del negocio + fecha actual + top-5 chunks RAG relevantes para la query del usuario.

**44. Que contiene static_knowledge y como lo usa el agente?**
Es un campo JSON en BusinessProfile con informacion estatica del negocio: sector, servicios, horario, tono, metodos de pago, politica de cancelacion. Lo usa el Wizard para configurar el negocio y los agentes proactivos para personalizar sus acciones.

**45. Como maneja el agente mensajes de voz?**
POST /upload_web_audio recibe el blob de audio WebM, lo guarda en disco, lo envia a Whisper-1 de OpenAI que devuelve el texto transcrito, y ese texto se pasa a run_agent() como si fuera un mensaje de texto normal. El agente no sabe si el input fue voz o texto.

**46. Como maneja el agente imagenes subidas por el usuario?**
Si media_url esta presente y admin_redactor esta en active_agents, el AgentExecutor hace dispatch directo a AdminAssistantAgent sin pasar por el ciclo LLM normal. El agente de imagen usa GPT-4o Vision para extraer el contenido y genera el PDF.

**47. Que ocurre si el RAG no encuentra ningun chunk relevante?**
retrieve_chunks() retorna una lista vacia. _build_rag_system_prompt() detecta esa lista vacia y devuelve solo el system prompt base sin seccion de contexto. El agente responde con su conocimiento general pero sin informacion especifica del negocio.

**48. Por que top_k=5 en el RAG y no mas?**
Balance entre contexto relevante y ruido en el prompt. Con top_k=1 se pierde cobertura; con top_k=20 se dilluye el prompt con fragmentos poco relevantes que pueden confundir al modelo. 5 es el valor documentado como optimo para la mayoria de casos RAG.

**49. Como se pasa el historial de conversacion al LLM?**
HistoryService.get_recent_history() devuelve los ultimos 10 mensajes como lista de dicts {role, content}. Se insertan entre el system message y el mensaje actual en el array messages antes de la llamada a la API.

**50. Por que solo 10 mensajes del historial y no todos?**
GPT-4o tiene un contexto de 128k tokens pero cada token tiene coste. 10 mensajes cubren la conversacion reciente relevante manteniendo el coste bajo. Los 50 mensajes completos se conservan en BD para el auto-cleanup pero solo 10 van al LLM.

**51. Que hace el auto-cleanup del historial?**
Cuando el total de mensajes de un usuario supera MAX_HISTORY (50), se borran los mas antiguos hasta dejar KEEP_COUNT (40). Esto evita que la tabla ChatMessage crezca indefinidamente en BD, manteniendo las conversaciones recientes.

**52. Por que los mensajes de tool deben incluir tool_call_id?**
Es un requisito del protocolo de OpenAI Function Calling. Si el mensaje de rol "tool" no incluye tool_call_id y name coincidentes con el tool_call original, la API devuelve error 400. Es una de las restricciones mas criticas del sistema.

**53. Como funciona el Consejo Pyme tecnicamente?**
CouncilManager usa AsyncOpenAI para hacer llamadas async. Tres agentes (Socio/Tiger, Gestor/Owl, Coach/Rocket) opinan secuencialmente en ronda 1, debaten en ronda 2 viendo las opiniones de los otros, y en ronda 3 el Secretario sintetiza un Plan de Accion. Todo se emite via SSE al frontend.

**54. Por que las llamadas del Consejo son secuenciales y no paralelas?**
Para mantener el efecto dramatico de "pensando en tiempo real". Con asyncio.gather() podrian paralelizarse las 3 llamadas de cada ronda, pero se perderia el streaming progresivo que hace la UX mas atractiva para la demo del TFM.

**55. Como funciona el streaming SSE en el Consejo Pyme?**
Flask usa stream_with_context() + Response(generator, mimetype="text/event-stream"). El generator es una corrutina async que hace yield de cada evento (typing, message, divider, plan) serializado como JSON. El frontend usa EventSource API para recibirlos.

---

## CATEGORIA 4: RAG Y EMBEDDINGS (56-70)

**56. Que es RAG y por que es mejor que fine-tuning para este caso?**
RAG (Retrieval Augmented Generation) recupera informacion relevante en tiempo real antes de cada llamada al LLM. Fine-tuning reentrenaria el modelo con los datos del negocio, lo que es costoso (miles de euros), estatico (requiere reentrenar ante cambios) y no escala por usuario.

**57. Como funciona el chunking recursivo que usas?**
El texto se divide usando una jerarquia de separadores: primero por parrafos (doble salto de linea), luego por lineas, luego por frases (punto+espacio), luego por palabras, y finalmente caracter a caracter como caso base. Cada nivel solo se aplica si el chunk supera CHUNK_SIZE.

**58. Por que CHUNK_SIZE=1600 caracteres?**
Equivale a aproximadamente 400 tokens (ratio ~4 chars/token). Es el sweet spot documentado para text-embedding-3-small: suficiente contexto semantico por fragmento sin diluir la especificidad del embedding.

**59. Por que CHUNK_OVERLAP=400 caracteres (25%)?**
Evita perder informacion en los limites de fragmento. Si una idea clave queda partida entre dos chunks, el solapamiento garantiza que al menos uno de ellos la contiene completa. El rango optimo documentado es 20-25% del chunk size.

**60. Por que conviertes PDFs a Markdown antes de chunkear?**
pymupdf4llm.to_markdown() preserva la estructura jerarquica del PDF (titulos, listas, tablas). El chunking recursivo puede entonces usar los saltos de linea dobles de Markdown para partir por parrafos reales en lugar de por posicion arbitraria de caracter.

**61. Como funciona la busqueda por similitud coseno en pgvector?**
Se vectoriza la query del usuario con text-embedding-3-small (1536 dimensiones). pgvector calcula la distancia coseno entre ese vector y todos los embeddings almacenados del usuario, ordenando por similitud ascendente. Se devuelven los top_k=5 mas cercanos.

**62. Por que distancia coseno y no euclidiana?**
Los embeddings de OpenAI estan normalizados (norma L2=1), lo que hace que distancia coseno y euclidiana sean equivalentes matematicamente. La convencion de la industria es usar coseno para embeddings de texto, y pgvector lo implementa eficientemente con el operador <=>.

**63. Que dimension tienen los embeddings y por que?**
1536 dimensiones, fijado por el modelo text-embedding-3-small de OpenAI. No es configurable; es una caracteristica del modelo. El campo en BD es Vector(1536) declarado en el modelo SQLAlchemy con pgvector.

**64. Cuantos chunks puede tener un usuario en la BD?**
No hay limite implementado. Un documento PDF de 50 paginas podria generar ≈100-200 chunks. En produccion se necesitaria un limite por plan (ej: BASIC 500 chunks, PRO 5000 chunks) para controlar el coste de embeddings y el espacio en BD.

**65. Como indexas los chunks del Wizard (configuracion del negocio)?**
Cuando el usuario guarda el wizard, cada campo (sector, servicios, horario, tono) se indexa como un KnowledgeChunk separado con source_type="wizard". Esto permite al agente responder preguntas sobre el negocio basandose en lo que el propio empresario configuro.

**66. Que pasa si el usuario sube el mismo documento dos veces?**
Actualmente se crean chunks duplicados en BD. No hay verificacion de duplicados por hash de archivo. En produccion se anadiriia un campo source_hash (MD5/SHA256) y una verificacion antes de indexar.

**67. Como manejas el coste de los embeddings?**
text-embedding-3-small cuesta 0,02 USD por millon de tokens. Un chunk de 400 tokens cuesta 0,000008 USD. Indexar 100 chunks cuesta 0,0008 USD. Es un coste marginal minimo comparado con GPT-4o. Solo se generan embeddings en el momento de ingesta, no en cada consulta del usuario.

**68. Podrias usar un modelo de embeddings local en lugar de OpenAI?**
Si. Modelos como sentence-transformers (BERT-based) o nomic-embed-text pueden correr localmente con 0 coste de API. El trade-off es calidad ligeramente inferior en espanol y mayor complejidad de infraestructura (GPU recomendada para produccion).

**69. Como garantizas que el RAG no exponga informacion de un usuario a otro?**
Todas las queries de retrieve_chunks() filtran por user_phone: KnowledgeChunk.query.filter_by(user_phone=user_phone). Es imposible que los chunks de un negocio aparezcan en el contexto de otro.

**70. Que mejoras aplicarias al RAG en una version 2.0?**
Reranking con un modelo cross-encoder para mejorar la precision despues del retrieval inicial, indices HNSW en pgvector para busquedas sublineales en colecciones grandes, y evaluacion automatica de calidad RAG con metricas como RAGAS (faithfulness, answer relevancy).

---

## CATEGORIA 5: BASE DE DATOS Y MODELOS (71-80)

**71. Cuantos modelos de BD tiene el sistema y cuales son los principales?**
Aproximadamente 12 modelos: BusinessProfile (usuario/empresa), Appointment (citas), KnowledgeChunk (embeddings RAG), ChatMessage (historial), LLMCall (metricas IA), Ticket (facturas), Grant (subvenciones), SynergyMatch, Notification, ActivityLog, GeneratedDocument, Incident.

**72. Por que el identificador primario de BusinessProfile es user_phone y no un UUID?**
Herencia del diseno original con WhatsApp como canal principal, donde el telefono era el identificador natural. Es una deuda tecnica identificada: en produccion se migraria a UUID para desacoplar identidad de medio de contacto.

**73. Como manejas las relaciones entre modelos sin ForeignKey explicita en algunos casos?**
Por simplicidad del MVP, algunas relaciones usan strings de user_phone como referencia logica en lugar de ForeignKey con cascade. Esto facilita el desarrollo pero sacrifica integridad referencial a nivel de BD. En produccion se definiran FKs explicitamente.

**74. Que contiene el campo features de BusinessProfile?**
Un JSON con flags de funcionalidades habilitadas por plan: {"tickets_allowed": true, "bot_enabled": true, "marketing_enabled": false}. Permite activar/desactivar capacidades por usuario sin cambios de codigo.

**75. Como funciona el campo active_agents?**
Es un array JSON en BusinessProfile: ["grant_hunter", "networker", "post_sales_service"]. El scheduler itera sobre todos los usuarios y para cada agente verifica si su ID esta en este array antes de ejecutarlo.

**76. Que almacena ActivityLog y para que sirve?**
Registra cada accion de cada agente: agente (ej: "Calendar Agent"), accion (ej: "Cita agendada: Juan"), timestamp y user_phone. Se muestra en el dashboard como feed de actividad reciente del negocio.

**77. Como funciona GeneratedDocument?**
Almacena metadatos de los documentos generados por IA: user_phone, file_path (ruta fisica en servidor), doc_type (proposal/image/presentation/video), client_name y created_at. La ruta permite servirlos directamente desde /static/generated_docs/.

**78. Que es SynergyMatch y como se genera?**
Almacena pares de usuarios con oportunidad de negocio detectada por el SynergyAgent: user_a, user_b, score (0-100), reason y timestamp. Se crea cuando el agente detecta complementariedad entre los perfiles de gasto de dos negocios.

**79. Como manejas los datos sensibles como password_hash?**
Las contrasenas se almacenan como hash bcrypt (via werkzeug.security). Nunca se almacena la contrasena en texto plano. El campo se llama password_hash explicitamente para dejar claro en el codigo que es un hash.

**80. Por que usas JSON nativo de PostgreSQL en lugar de tablas relacionales para algunos datos?**
Flexibilidad y velocidad de iteracion. Campos como static_knowledge, features y agent_config varian entre negocios y evolucionan rapidamente. Con JSON evitas migraciones de schema en cada cambio de configuracion. El trade-off es que no puedes hacer queries SQL eficientes sobre esos campos.

---

## CATEGORIA 6: INFRAESTRUCTURA Y SEGURIDAD (81-90)

**81. Como proteges el acceso a la aplicacion?**
Login con email/password (hash bcrypt), session Flask con cookie firmada (SECRET_KEY), y decoradores de autenticacion en todas las rutas protegidas (verifican session['user_phone']). Rate limiting en login (5 intentos/minuto) para prevenir brute force.

**82. Que es VAPID y para que lo usas?**
Voluntary Application Server Identification. Es el protocolo de autenticacion para Web Push. Genera un par de claves publica/privada. La clave publica se comparte con el navegador al suscribirse; la privada firma las notificaciones push enviadas desde el servidor.

**83. Como funcionan las notificaciones Web Push?**
El navegador se suscribe al servicio push del sistema operativo y devuelve un PushSubscription JSON. Este se almacena en BusinessProfile.push_subscription. Cuando el servidor quiere notificar, usa pywebpush para enviar el mensaje firmado con VAPID al endpoint del navegador.

**84. Como proteges las claves de API (OpenAI, Runway, etc.)?**
Mediante variables de entorno definidas en el fichero .env (no versionado en git) y cargadas con python-dotenv. En Docker Compose se pasan como environment variables al contenedor. Nunca se hardcodean en el codigo fuente.

**85. Que logs genera el sistema y como los consultas?**
Python logging modulo con nivel WARNING en produccion. Los logs de Gunicorn incluyen access log (request/response). En Docker: docker logs ticketia_app. En produccion real se centralizarian con ELK Stack o CloudWatch.

**86. Como manejas los ficheros subidos por usuarios?**
Se almacenan en /static/uploads/ con nombres unicos (timestamp + nombre original). El directorio se monta como volumen Docker para persistencia entre reinicios. No hay validacion de tipo MIME exhaustiva en el MVP (deuda de seguridad).

**87. Que pasaria si un usuario sube un fichero malicioso?**
El sistema actualmente no valida el contenido del fichero mas alla de la extension. Un fichero malicioso podria almacenarse en disco. En produccion se necesita: validacion MIME real, escaneo antivirus (ClamAV), limite de tamano (ya implementado parcialmente), y sandbox de procesamiento.

**88. Como implementas el logout de forma segura?**
session.clear() elimina todos los datos de sesion del servidor. La cookie del cliente queda invalidada porque no coincide con ninguna sesion activa. Flask usa cookies firmadas, no almacenamiento server-side, por lo que el "logout" es simplemente dejar de reconocer esa cookie.

**89. Tienes CSRF protection?**
Flask-WTF proporciona CSRF protection para formularios. En el MVP, las llamadas AJAX al API de chat usan el patron fetch() con credenciales de sesion, lo que tiene cierta proteccion natural. En produccion se implementaria CSRF token explicito en todas las llamadas POST.

**90. Como manejas los errores 500 en produccion?**
El AgentExecutor tiene un try/except global que devuelve un mensaje amigable en lugar de exponer el stack trace al usuario. Flask tiene error handlers globales para 404 y 500. En produccion, los stack traces se loggean pero nunca se muestran al usuario final.

---

## CATEGORIA 7: NEGOCIO Y PREGUNTAS CRITICAS (91-100)

**91. El tribunal podria preguntarte: por que deberia un PYME pagarte a ti y no usar ChatGPT Plus directamente?**
ChatGPT Plus cuesta 20 USD/mes pero requiere que el empresario sepa formular prompts, no tiene acceso a su agenda propia, no genera PDFs profesionales automaticamente, no tiene agentes proactivos que trabajen solos, y no puede personalizarse con el conocimiento especifico del negocio.

**92. Que pasaria si un competidor con mas recursos copia el producto en 6 meses?**
El moat no esta en la tecnologia (que es reproducible) sino en la base de clientes, el conocimiento especifico de sector PYME, las integraciones verticales y la velocidad de iteracion. La estrategia seria crecer rapidamente en nicho antes de que un grande lo detecte como oportunidad.

**93. Por que deberia el tribunal creer que esto es viable y no un proyecto de laboratorio?**
La arquitectura esta en produccion real con Docker, la BD es PostgreSQL de produccion, el sistema maneja usuarios reales, y cada componente tiene justificacion tecnica y economica documentada. El LLMTracker prueba que el coste es controlable y predecible.

**94. Cual es la mayor debilidad tecnica del sistema?**
Los background threads (threading.Thread) para tareas asincronas. Si el proceso Flask muere, los jobs en vuelo se pierden sin posibilidad de recovery. Celery+Redis es la solucion obvia y es el primer item del roadmap post-TFM.

**95. Que tan dificil seria portar esto a otro proveedor de LLM si OpenAI cierra o sube precios?**
El AgentExecutor usa el cliente de OpenAI directamente. La abstraccion get_openai_client() facilita el cambio, pero habria que adaptar el formato de TOOLS_SCHEMA (que es especifico de OpenAI) al formato del nuevo proveedor (Anthropic usa tool_use, Google usa functionDeclarations).

**96. Que aprendiste de este TFM que no sabias antes de empezarlo?**
La complejidad de gestionar estado en sistemas distribuidos (race conditions en Docker, threading vs async), la importancia de la abstraccion del proveedor LLM, y que el mayor desafio de un producto IA no es el modelo sino la integracion con el mundo real (BD, notificaciones, archivos).

**97. Como medirias el exito del TFM mas alla de la nota?**
Con tres metricas: (1) funcionalidad completa y demostrable del golden path, (2) justificacion tecnica solida de cada decision de diseno, (3) modelo de negocio creible con economica unitaria positiva. Los tres han sido alcanzados.

**98. Si tuvieras 6 meses mas, que harias primero?**
En orden de prioridad: (1) Celery+Redis para tareas async, (2) streaming SSE en el chat principal, (3) integracion con WhatsApp Business API, (4) evaluacion automatica de calidad RAG, (5) tier de precios con Stripe y trial automatico.

**99. Que tiene este TFM de investigacion original vs implementacion de tecnologias existentes?**
La originalidad esta en la combinacion e integracion: RAG + Tool Calling + MCP + agentes proactivos + Consejo multi-agente en una plataforma vertical cohesionada para PYMEs. Cada componente existe por separado en la literatura; la arquitectura integradora y el producto resultante son la contribucion.

**100. Que consejo darias a alguien que empieza un TFM de IA aplicada?**
Empieza con el caso de uso mas estrecho posible y demuestralo funcionando antes de ampliar. La tentacion de anadir features es el mayor enemigo. Un golden path robusto impresiona mas que diez features a medias. Y mide todo desde el primer dia: latencia, coste, errores.
"""

with open('preguntas_tribunal_tfm.md', 'w', encoding='utf-8') as f:
    f.write(preguntas)

print(f"Archivo generado: preguntas_tribunal_tfm.md ({len(preguntas)} caracteres, 100 preguntas)")
