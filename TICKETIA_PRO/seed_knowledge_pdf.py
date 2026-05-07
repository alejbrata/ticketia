"""
seed_knowledge_pdf.py

Genera un PDF de base de conocimiento para Demo Business S.L.
y lo guarda en static/uploads/knowledge/+34600000001/demo_business_knowledge.pdf

Uso: python seed_knowledge_pdf.py
"""

import os
from pathlib import Path
from fpdf import FPDF, XPos, YPos


OUTPUT_PATH = Path("static/uploads/knowledge/+34600000001/demo_business_knowledge.pdf")


class KnowledgePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Demo Business S.L. - Base de Conocimiento Corporativa", align="C")
        self.ln(2)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

    def section_title(self, title):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(30, 60, 120)
        self.set_text_color(255, 255, 255)
        self.cell(0, 9, f"  {title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def subsection_title(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 60, 120)
        self.multi_cell(0, 7, title)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text, indent=8):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        x = self.get_x()
        y = self.get_y()
        self.set_x(x + indent)
        self.multi_cell(0, 6, f"- {text}")
        self.ln(1)


def build_pdf():
    pdf = KnowledgePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(14, 18, 14)
    pdf.add_page()

    # -------------------------------------------------------------------------
    # Portada / Titulo
    # -------------------------------------------------------------------------
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 12, "Demo Business S.L.", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Dossier Corporativo y Base de Conocimiento", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Soluciones de Inteligencia Artificial Generativa para Empresas", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_draw_color(30, 60, 120)
    pdf.set_line_width(0.8)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(8)

    # -------------------------------------------------------------------------
    # 1. Sobre la empresa
    # -------------------------------------------------------------------------
    pdf.section_title("1. Sobre la Empresa")

    pdf.body_text(
        "Demo Business S.L. es una empresa espanola especializada en el desarrollo e implantacion de soluciones "
        "de inteligencia artificial generativa para pequenas y medianas empresas (pymes) y startups tecnologicas. "
        "Fundada en 2023, la compania nace con una vision clara: hacer accesible el poder de los grandes modelos "
        "de lenguaje (LLM) a organizaciones que, hasta ahora, no disponian de los recursos tecnicos ni economicos "
        "para beneficiarse de esta revolucion tecnologica."
    )
    pdf.body_text(
        "Con sede en Madrid, Demo Business S.L. cuenta con un equipo multidisciplinar de 8 especialistas en "
        "ingenieria de software, machine learning, arquitectura de datos y diseno de experiencia de usuario. "
        "El equipo combina experiencia academica de alto nivel con anos de practica en proyectos de IA para "
        "sectores como la salud, el derecho, la logistica, el comercio electronico y los servicios financieros."
    )
    pdf.body_text(
        "Mision: Democratizar la inteligencia artificial generativa para que cualquier empresa, "
        "independientemente de su tamano, pueda automatizar procesos, mejorar la atencion al cliente y tomar "
        "decisiones mas inteligentes basadas en sus propios datos."
    )
    pdf.body_text(
        "Vision: Convertirnos en el referente tecnologico en IA generativa para pymes en el mercado iberico, "
        "ampliando progresivamente nuestra presencia a Latinoamerica a partir de 2025."
    )
    pdf.body_text(
        "Datos registrales: Razon social: Demo Business S.L. | CIF: B-12345678 | Domicilio social: "
        "Calle Gran Via 28, 3a planta, 28013 Madrid, Espana | Registro Mercantil de Madrid, Tomo 44.123, "
        "Folio 87, Hoja M-789456."
    )

    # -------------------------------------------------------------------------
    # 2. Servicios
    # -------------------------------------------------------------------------
    pdf.section_title("2. Servicios")

    pdf.subsection_title("2.1 Desarrollo de Chatbots Inteligentes")
    pdf.body_text(
        "Disenamos e implementamos asistentes conversacionales de ultima generacion basados en modelos como "
        "GPT-4o de OpenAI y Claude de Anthropic. Nuestros chatbots no son simples arboles de decision: "
        "comprenden el lenguaje natural, mantienen el contexto de la conversacion, consultan bases de datos "
        "en tiempo real y escalan sin problema. Ofrecemos integraciones nativas con los principales canales "
        "de comunicacion empresarial: widget para sitio web, API REST para aplicaciones internas, WhatsApp "
        "Business, Slack, Microsoft Teams y Telegram."
    )
    pdf.body_text(
        "Cada chatbot incluye un panel de administracion donde el cliente puede revisar conversaciones, "
        "ajustar la personalidad del asistente, anadir nueva informacion y consultar estadisticas de uso "
        "(numero de conversaciones, tasa de resolucion, temas mas frecuentes). La configuracion inicial "
        "incluye entrenamiento con la documentacion interna del cliente, definicion de tonos de voz y "
        "restricciones de contenido segun las politicas de la empresa."
    )

    pdf.subsection_title("2.2 Sistemas RAG (Retrieval-Augmented Generation)")
    pdf.body_text(
        "Los sistemas RAG permiten que un modelo de lenguaje responda preguntas basandose exclusivamente en "
        "los documentos internos de la empresa: manuales, contratos, expedientes, normativas, FAQs, "
        "historiales de soporte, etc. La arquitectura tipica consta de tres capas: ingesta y segmentacion "
        "de documentos (PDF, Word, Excel, HTML), indexacion en una base de datos vectorial como pgvector "
        "o Pinecone, y un pipeline de recuperacion semantica que alimenta al LLM con los fragmentos mas "
        "relevantes antes de generar cada respuesta."
    )
    pdf.body_text(
        "Esto elimina las alucinaciones tipicas de los LLM puros, ya que el modelo solo puede responder "
        "con informacion verificable procedente de los documentos del cliente. Ademas, cada respuesta "
        "incluye referencias a los fragmentos de origen, lo que facilita la auditoria y la confianza del "
        "usuario final. Nuestros sistemas RAG soportan actualizacion incremental: cuando el cliente sube "
        "un nuevo documento, este se indexa automaticamente en minutos sin necesidad de reentrenar ningun modelo."
    )

    pdf.subsection_title("2.3 Automatizacion de Procesos con IA")
    pdf.body_text(
        "Identificamos los procesos repetitivos y con alto volumen de datos de texto en la empresa del "
        "cliente y los automatizamos mediante pipelines de IA. Los casos de uso mas habituales son: "
        "extraccion y validacion de datos de facturas y albaranes, clasificacion y enrutamiento automatico "
        "de correos electronicos entrantes, generacion de informes periodicos a partir de datos estructurados, "
        "revision y resumen de contratos, y triaje de incidencias de soporte tecnico."
    )
    pdf.body_text(
        "La integracion con los sistemas existentes del cliente (ERP, CRM, herramientas de helpdesk) se "
        "realiza mediante webhooks, APIs REST o conectores nativos segun la plataforma. Todo el pipeline "
        "queda documentado y el cliente recibe formacion para poder supervisarlo y ajustarlo de forma autonoma."
    )

    pdf.subsection_title("2.4 Fine-Tuning y Evaluacion de Modelos")
    pdf.body_text(
        "Cuando los modelos de proposito general no son suficientes para el caso de uso especifico del "
        "cliente (por ejemplo, jerga sectorial muy especializada o formatos de salida muy rigidos), "
        "ofrecemos servicios de fine-tuning sobre modelos base open-source o sobre la API de OpenAI. "
        "El proceso incluye: definicion del objetivo y metricas de exito, construccion y curacion del "
        "dataset de entrenamiento, entrenamiento del modelo, evaluacion automatizada con LLM-as-judge "
        "y metricas clasicas (BLEU, ROUGE, F1), y despliegue en infraestructura del cliente o en la nube."
    )
    pdf.body_text(
        "Tambien ofrecemos auditorias de modelos ya desplegados: si el cliente tiene un sistema de IA "
        "en produccion y quiere saber si esta funcionando correctamente, realizamos un estudio de calidad "
        "con casos de prueba representativos, analisis de sesgos y recomendaciones de mejora."
    )

    pdf.subsection_title("2.5 Consultoria Estrategica en IA")
    pdf.body_text(
        "Muchas empresas saben que quieren usar IA pero no saben por donde empezar. Nuestro servicio de "
        "consultoria estrategica ayuda a identificar los casos de uso de mayor impacto y menor riesgo para "
        "iniciar el camino de la transformacion digital con IA generativa. El servicio incluye: auditoria "
        "de procesos internos y deteccion de oportunidades de automatizacion, evaluacion de la madurez "
        "de datos de la empresa, diseno del roadmap de adopcion de IA para 12-24 meses, analisis de "
        "viabilidad tecnica y economica de cada iniciativa, y talleres de formacion para equipos directivos "
        "y tecnicos."
    )

    # -------------------------------------------------------------------------
    # 3. Paquetes y precios
    # -------------------------------------------------------------------------
    pdf.section_title("3. Paquetes y Precios")

    pdf.body_text(
        "Ofrecemos paquetes predefinidos para facilitar la decision de compra, aunque todos nuestros "
        "proyectos pueden personalizarse. Los precios indicados no incluyen IVA (21%)."
    )

    pdf.subsection_title("Paquete Starter - 1.500 EUR")
    pdf.body_text(
        "Ideal para empresas que quieren dar sus primeros pasos con un asistente conversacional. Incluye: "
        "desarrollo de un chatbot basico basado en GPT-4o o Claude con personalidad y tono definidos por "
        "el cliente, entrenamiento inicial con hasta 20 documentos o paginas de informacion corporativa, "
        "una integracion en el canal elegido (web, WhatsApp o Telegram), panel de administracion basico, "
        "y soporte tecnico durante 30 dias tras la entrega. Tiempo de desarrollo estimado: 2-3 semanas."
    )

    pdf.subsection_title("Paquete Professional - 4.500 EUR")
    pdf.body_text(
        "Disenado para empresas que necesitan una solucion mas robusta con capacidad de consultar "
        "documentacion interna. Incluye todo lo del paquete Starter mas: sistema RAG completo con "
        "indexacion de hasta 500 documentos, hasta 3 integraciones en canales distintos, panel de "
        "metricas avanzado con estadisticas de uso y calidad de respuestas, alertas automaticas ante "
        "respuestas de baja confianza, y soporte tecnico prioritario durante 90 dias. "
        "Tiempo de desarrollo estimado: 4-6 semanas."
    )

    pdf.subsection_title("Paquete Enterprise - Desde 12.000 EUR")
    pdf.body_text(
        "Solucion completamente a medida para organizaciones con requisitos avanzados de seguridad, "
        "escala o integracion. Incluye: arquitectura disenada especificamente para el caso de uso del "
        "cliente, numero ilimitado de documentos e integraciones, despliegue en infraestructura privada "
        "del cliente (on-premise o cloud dedicado), SLA de disponibilidad del 99.9%, formacion completa "
        "del equipo tecnico y de negocio del cliente, soporte tecnico anual con gestor de cuenta asignado, "
        "y revisiones trimestrales de rendimiento del sistema. El precio final se determina tras el "
        "proceso de Discovery."
    )

    pdf.subsection_title("Consultoria por Horas - 150 EUR/hora (minimo 10 horas)")
    pdf.body_text(
        "Para clientes que necesitan asesoria puntual o acompanamiento en proyectos propios. Las horas "
        "pueden utilizarse para revision de arquitecturas, sesiones de formacion tecnica, evaluacion de "
        "modelos o cualquier otra necesidad de consultoria relacionada con IA generativa. Las bolsas de "
        "horas tienen una validez de 6 meses desde la fecha de compra."
    )

    # -------------------------------------------------------------------------
    # 4. Tecnologias
    # -------------------------------------------------------------------------
    pdf.section_title("4. Stack Tecnologico")

    pdf.body_text(
        "Seleccionamos las herramientas mas adecuadas para cada proyecto, priorizando siempre la fiabilidad "
        "en produccion, el coste operativo y la capacidad del cliente para mantener el sistema de forma "
        "autonoma. A continuacion se describen las tecnologias principales que forman parte de nuestro arsenal:"
    )
    pdf.body_text(
        "Modelos de lenguaje: OpenAI GPT-4o (principal para proyectos con requisitos de razonamiento complejo "
        "y multimodalidad), Anthropic Claude 3.5 Sonnet y Claude 3 Haiku (para casos de uso con alto volumen "
        "de tokens o cuando se requiere menor latencia), y modelos open-source como Llama 3 o Mistral para "
        "despliegues en infraestructura privada sin dependencia de APIs externas."
    )
    pdf.body_text(
        "Orquestacion y pipelines: LangChain y LangGraph para la construccion de agentes y cadenas de "
        "razonamiento multi-paso. LlamaIndex para pipelines RAG de alta performance. FastAPI como framework "
        "backend para exponer las capacidades de IA a traves de APIs REST seguras y documentadas."
    )
    pdf.body_text(
        "Bases de datos vectoriales: pgvector sobre PostgreSQL para proyectos donde el cliente ya dispone "
        "de infraestructura PostgreSQL, Pinecone para proyectos con requisitos de escala masiva, y Chroma "
        "para prototipos y entornos de desarrollo."
    )
    pdf.body_text(
        "Frontend y experiencia de usuario: React con TypeScript para paneles de administracion y widgets "
        "de chat embebibles. Tailwind CSS para diseno responsivo. Next.js para aplicaciones web completas "
        "cuando el proyecto lo requiere."
    )
    pdf.body_text(
        "Infraestructura y DevOps: Docker y Docker Compose para contenerizacion y reproducibilidad de "
        "entornos. GitHub Actions para CI/CD automatizado con tests, linting y despliegue continuo. "
        "AWS (EC2, ECS, S3, RDS) y Azure (App Service, Azure OpenAI, Blob Storage) como proveedores "
        "cloud principales. Terraform para infraestructura como codigo en proyectos Enterprise."
    )
    pdf.body_text(
        "Observabilidad y MLOps: LangSmith para trazabilidad y evaluacion de pipelines LLM, Prometheus "
        "y Grafana para metricas de sistema, y Sentry para monitorizacion de errores en produccion."
    )

    # -------------------------------------------------------------------------
    # 5. Proceso de trabajo
    # -------------------------------------------------------------------------
    pdf.section_title("5. Proceso de Trabajo")

    pdf.body_text(
        "Todos nuestros proyectos siguen una metodologia iterativa y colaborativa dividida en cinco fases. "
        "Este enfoque garantiza que el producto final se ajusta exactamente a las necesidades del cliente "
        "y que no existen sorpresas en ningun punto del proceso."
    )

    pdf.subsection_title("Fase 1: Discovery (1 semana)")
    pdf.body_text(
        "El proyecto comienza con una fase de descubrimiento en la que nuestro equipo se sumerge en el "
        "negocio del cliente. Realizamos entrevistas con los stakeholders clave, analizamos los procesos "
        "actuales, revisamos la documentacion existente y definimos de forma precisa los objetivos del "
        "proyecto, los indicadores clave de rendimiento (KPIs) que mediran el exito, y los criterios de "
        "aceptacion. Al final de esta fase, el cliente recibe un documento de alcance detallado que "
        "sirve de base contractual para el resto del proyecto."
    )

    pdf.subsection_title("Fase 2: Diseno Tecnico (1 semana)")
    pdf.body_text(
        "Con los requisitos claros, el equipo tecnico disena la arquitectura de la solucion: seleccion "
        "de modelos, estructura de la base de datos vectorial, flujo de datos, plan de integraciones y "
        "estrategia de seguridad. El cliente revisa y aprueba el diseno tecnico antes de que comience "
        "el desarrollo, lo que evita retrabajo costoso en fases posteriores."
    )

    pdf.subsection_title("Fase 3: Desarrollo (2-6 semanas segun complejidad)")
    pdf.body_text(
        "El desarrollo se realiza en sprints semanales. Al final de cada sprint, el cliente tiene acceso "
        "a un entorno de staging donde puede probar las funcionalidades implementadas y dar feedback. "
        "Utilizamos GitHub para el control de versiones, con revisiones de codigo (code reviews) "
        "sistematicas y tests automatizados que garantizan la calidad del codigo entregado."
    )

    pdf.subsection_title("Fase 4: Testing y Evaluacion (1 semana)")
    pdf.body_text(
        "Antes del despliegue en produccion, el sistema pasa por una bateria exhaustiva de pruebas: "
        "tests funcionales, tests de carga, evaluacion de calidad de las respuestas del LLM mediante "
        "LLM-as-judge con un conjunto de casos de prueba representativos acordados con el cliente, "
        "y pruebas de seguridad basicas (inyeccion de prompts, exfiltracion de datos). Los resultados "
        "de la evaluacion se comparten con el cliente en un informe detallado."
    )

    pdf.subsection_title("Fase 5: Despliegue y Formacion (1 semana)")
    pdf.body_text(
        "El sistema se despliega en el entorno de produccion del cliente. Se realiza una sesion de "
        "formacion para el equipo tecnico (administracion del sistema, monitorizacion, actualizacion "
        "de documentos) y otra para los usuarios finales o el equipo de negocio (uso del panel de "
        "administracion, interpretacion de metricas, proceso para reportar incidencias). "
        "El cliente recibe documentacion tecnica completa y un video-tutorial grabado."
    )

    # -------------------------------------------------------------------------
    # 6. Casos de exito
    # -------------------------------------------------------------------------
    pdf.section_title("6. Casos de Exito")

    pdf.subsection_title("Caso 1: Clinica Dental en Barcelona - Reduccion del 70% en Llamadas de Recepcion")
    pdf.body_text(
        "Una clinica dental con tres consultorios en Barcelona recibia mas de 200 llamadas diarias para "
        "consultar horarios, reservar citas, preguntar por precios y solicitar informacion sobre tratamientos. "
        "El personal de recepcion dedicaba el 80% de su jornada a responder preguntas repetitivas, lo que "
        "generaba largas esperas y errores frecuentes en la gestion de citas."
    )
    pdf.body_text(
        "Implementamos un chatbot inteligente integrado en su pagina web y en WhatsApp Business, entrenado "
        "con toda la informacion de la clinica: catalogo de tratamientos, precios orientativos, horarios "
        "por especialidad, politica de cancelaciones y preguntas frecuentes de pacientes. El chatbot "
        "tambien conectaba con su software de gestion para consultar disponibilidad en tiempo real y "
        "confirmar citas directamente en el calendario."
    )
    pdf.body_text(
        "Resultado tras 60 dias de operacion: reduccion del 70% en el volumen de llamadas telefonicas "
        "relacionadas con informacion general, tiempo medio de respuesta a pacientes de 48 horas a "
        "menos de 2 minutos, y valoracion de satisfaccion de pacientes del chatbot de 4.2 sobre 5."
    )

    pdf.subsection_title("Caso 2: Distribuidora Logistica en Valencia - Ahorro de 15 Horas Semanales")
    pdf.body_text(
        "Una empresa distribuidora con mas de 300 proveedores recibia diariamente entre 80 y 120 facturas "
        "en PDF por correo electronico. El departamento de administracion tardaba una media de 8 minutos "
        "en procesar cada factura manualmente: extraer los datos, validarlos contra el pedido correspondiente "
        "en el ERP, y registrarlos. Esto representaba mas de 15 horas semanales de trabajo repetitivo "
        "con una tasa de error del 3%."
    )
    pdf.body_text(
        "Desarrollamos un pipeline de automatizacion que monitoriza la bandeja de entrada del email, "
        "descarga los PDFs adjuntos, extrae los campos clave (proveedor, NIF, numero de factura, fecha, "
        "lineas de detalle, importes, IVA) mediante un LLM especializado, valida los datos contra el ERP "
        "via API, y registra automaticamente la factura si todo es correcto o la envia a revision humana "
        "con el motivo del fallo claramente indicado."
    )
    pdf.body_text(
        "Resultado: reduccion del tiempo de procesamiento de 8 minutos a menos de 30 segundos por factura, "
        "ahorro de mas de 15 horas semanales en el departamento de administracion, tasa de error reducida "
        "al 0.4% (errores residuales que el sistema envia correctamente a revision humana)."
    )

    pdf.subsection_title("Caso 3: Despacho de Abogados en Madrid - RAG sobre Expedientes Juridicos")
    pdf.body_text(
        "Un despacho de abogados especializado en derecho mercantil acumulaba mas de 8.000 expedientes "
        "digitalizados en PDF y Word, distribuidos en carpetas de red sin estructura unificada. Los "
        "abogados perdian entre 1 y 2 horas al dia buscando precedentes, clausulas contractuales especificas "
        "o jurisprudencia relevante entre los expedientes propios del despacho."
    )
    pdf.body_text(
        "Implementamos un sistema RAG sobre la totalidad del archivo documental del despacho, desplegado "
        "en sus propios servidores para garantizar la confidencialidad absoluta de la informacion de sus "
        "clientes. El sistema permite realizar consultas en lenguaje natural como 'clausulas de penalizacion "
        "por incumplimiento en contratos de distribucion del sector retail' y obtener en segundos los "
        "fragmentos mas relevantes de los expedientes, con cita exacta del documento y pagina de origen."
    )
    pdf.body_text(
        "Resultado: reduccion del tiempo de busqueda documental de 90 minutos a menos de 3 minutos por "
        "consulta, adopcion del sistema por el 100% de los abogados del despacho en las primeras dos "
        "semanas, y estimacion del cliente de un ahorro de productividad equivalente a contratar un "
        "asistente documental a tiempo parcial."
    )

    # -------------------------------------------------------------------------
    # 7. Garantias y politica de servicio
    # -------------------------------------------------------------------------
    pdf.section_title("7. Garantias y Politica de Servicio")

    pdf.body_text(
        "En Demo Business S.L. nos comprometemos con resultados reales y medibles. Por eso ofrecemos "
        "las siguientes garantias contractuales en todos nuestros proyectos:"
    )

    pdf.subsection_title("Revisiones Ilimitadas durante el Desarrollo")
    pdf.body_text(
        "Durante la fase de desarrollo, el cliente puede solicitar tantas revisiones y ajustes como "
        "necesite sin coste adicional, siempre que no impliquen un cambio de alcance sustancial respecto "
        "al documento de alcance aprobado en la fase de Discovery. Las solicitudes de cambio de alcance "
        "se evaluan y presupuestan por separado de forma transparente."
    )

    pdf.subsection_title("Garantia de Funcionamiento de 90 Dias Post-Entrega")
    pdf.body_text(
        "Una vez entregado el proyecto en produccion, Demo Business S.L. garantiza el correcto "
        "funcionamiento del sistema durante 90 dias calendario. Cualquier bug o mal funcionamiento "
        "que no sea consecuencia de cambios realizados por el propio cliente sera corregido sin coste "
        "adicional en un plazo maximo de 5 dias laborables desde la notificacion."
    )

    pdf.subsection_title("Politica de Devolucion Parcial por KPIs No Alcanzados")
    pdf.body_text(
        "Si en el contrato se establecieron KPIs cuantificables de exito (por ejemplo, porcentaje de "
        "consultas resueltas automaticamente, reduccion de tiempo de proceso, etc.) y a los 90 dias de "
        "uso en produccion dichos KPIs no se han alcanzado en al menos un 80% de lo acordado, el cliente "
        "tiene derecho a una devolucion del 50% del importe total del proyecto. Esta politica aplica "
        "unicamente cuando el cliente ha seguido las recomendaciones de uso y no ha realizado "
        "modificaciones no autorizadas sobre el sistema."
    )

    pdf.subsection_title("SLA: Respuesta en 24 Horas Laborables para Incidencias")
    pdf.body_text(
        "Para todos los proyectos en periodo de garantia o con contrato de mantenimiento activo, "
        "Demo Business S.L. se compromete a acusar recibo de cualquier incidencia reportada en un "
        "maximo de 24 horas laborables y a proporcionar una estimacion de resolucion. Las incidencias "
        "criticas (sistema completamente inoperativo) tienen un objetivo de resolucion de 48 horas "
        "laborables. El canal oficial de reporte de incidencias es el correo soporte@demobusiness.ai."
    )

    # -------------------------------------------------------------------------
    # 8. Preguntas frecuentes (FAQ)
    # -------------------------------------------------------------------------
    pdf.section_title("8. Preguntas Frecuentes (FAQ)")

    faqs = [
        (
            "P: ¿Cuanto tiempo tarda en estar listo mi proyecto?",
            "R: Depende de la complejidad. Un chatbot basico del paquete Starter puede estar listo en 2-3 semanas. "
            "Un sistema RAG con el paquete Professional tarda entre 4 y 6 semanas. Los proyectos Enterprise se "
            "dimensionan individualmente durante la fase de Discovery, pero raramente superan los 3 meses para "
            "el primer modulo funcional. Siempre damos una estimacion detallada y comprometida antes de firmar el contrato."
        ),
        (
            "P: ¿Necesito tener infraestructura tecnologica propia?",
            "R: No es imprescindible. Para los paquetes Starter y Professional, la solucion puede desplegarse "
            "en nuestra infraestructura cloud gestionada incluida en el precio. Para el paquete Enterprise o "
            "si el cliente tiene requisitos especificos de privacidad de datos, el despliegue puede realizarse "
            "en la infraestructura del cliente (servidores propios o cuenta cloud del cliente). En cualquier "
            "caso, asesoramos sobre la opcion mas conveniente desde el punto de vista tecnico y economico."
        ),
        (
            "P: ¿Es segura mi informacion y la de mis clientes?",
            "R: La seguridad es una prioridad absoluta. Todos los datos se transmiten cifrados mediante TLS 1.3. "
            "Cuando se utilizan APIs de terceros como OpenAI, los datos se procesan bajo los acuerdos de "
            "procesamiento de datos (DPA) de dichos proveedores, que cumplen con el RGPD. Para clientes con "
            "requisitos de maxima confidencialidad (sector legal, medico, financiero), recomendamos el "
            "despliegue con modelos open-source en infraestructura privada, donde ningun dato sale de los "
            "servidores del cliente. Firmamos NDA antes del inicio de cualquier proyecto."
        ),
        (
            "P: ¿Puedo integrar la solucion con el software que ya uso?",
            "R: Generalmente si. Siempre que el software existente disponga de una API o webhooks, la "
            "integracion es factible. Tenemos experiencia integrando con los CRMs mas comunes (Salesforce, "
            "HubSpot, Zoho), ERPs (SAP, Odoo, Sage), herramientas de helpdesk (Zendesk, Freshdesk), "
            "plataformas de ecommerce (Shopify, WooCommerce) y suites offimaticas (Google Workspace, "
            "Microsoft 365). Si el software no tiene API publica, evaluamos alternativas como la extraccion "
            "de datos desde exports o bases de datos directas."
        ),
        (
            "P: ¿Que pasa si la IA comete errores o da respuestas incorrectas?",
            "R: Ningun sistema de IA es perfecto, y trabajamos con total transparencia sobre esto. Para "
            "minimizar errores, implementamos mecanismos como el sistema RAG (que ancla las respuestas en "
            "documentos verificados), umbrales de confianza (si el sistema no esta seguro, escala a un "
            "humano en lugar de inventar una respuesta), y evaluacion continua de calidad. Ademas, el "
            "cliente puede revisar todas las conversaciones desde el panel de administracion y reportar "
            "respuestas incorrectas para mejorar el sistema. Durante la garantia de 90 dias, corregimos "
            "sin coste los patrones de error que se detecten."
        ),
        (
            "P: ¿Ofreceis formacion a nuestro equipo para usar y mantener el sistema?",
            "R: Si, la formacion esta incluida en todos los paquetes. Al finalizar el proyecto, realizamos "
            "una sesion de formacion practica para el equipo tecnico (configuracion, monitorizacion, "
            "actualizacion de documentos) y otra para los usuarios de negocio (uso del panel, interpretacion "
            "de metricas, proceso de reporte de problemas). Ademas, entregamos documentacion escrita y "
            "un video-tutorial grabado. Para el paquete Enterprise, la formacion es mas extensa e incluye "
            "sesiones adicionales de repaso a los 30 y 90 dias post-entrega."
        ),
        (
            "P: ¿Como se mide el exito del proyecto?",
            "R: Antes de empezar cualquier proyecto, definimos conjuntamente con el cliente los KPIs "
            "especificos que mediran el exito. Estos se recogen en el documento de alcance y forman "
            "parte del contrato. Los KPIs tipicos incluyen: porcentaje de consultas resueltas "
            "automaticamente, reduccion del tiempo de proceso, reduccion del volumen de trabajo manual, "
            "puntuacion de satisfaccion de usuarios, tasa de adopcion del sistema por el equipo, etc. "
            "A los 90 dias de uso en produccion, realizamos una revision formal con el cliente para "
            "evaluar el cumplimiento de los KPIs."
        ),
        (
            "P: ¿Haceis proyectos para startups con presupuesto limitado?",
            "R: Si. Entendemos que las startups tienen restricciones presupuestarias y valoramos trabajar "
            "con ellas en etapas tempranas. Ofrecemos la posibilidad de abordar proyectos por fases, "
            "empezando por un MVP (producto minimo viable) con el paquete Starter y escalando "
            "progresivamente. Tambien tenemos un programa especial para startups aceleradas o con "
            "financiacion publica (ENISA, Neotec) que incluye condiciones de pago adaptadas. "
            "Consultadnos sin compromiso en contacto@demobusiness.ai."
        ),
    ]

    for question, answer in faqs:
        pdf.subsection_title(question)
        pdf.body_text(answer)

    # -------------------------------------------------------------------------
    # 9. Contacto
    # -------------------------------------------------------------------------
    pdf.section_title("9. Informacion de Contacto")

    pdf.body_text(
        "Estamos a tu disposicion para resolver cualquier duda, realizar una demostracion sin compromiso "
        "o comenzar la fase de Discovery de tu proyecto. Puedes contactarnos a traves de cualquiera de "
        "los siguientes canales:"
    )

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 7, "Correo electronico (consultas comerciales y soporte):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "   contacto@demobusiness.ai", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 7, "   soporte@demobusiness.ai", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Telefono:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "   +34 91 000 00 01 (lunes a viernes, 9:00-18:00 CET)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Direccion:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "   Calle Gran Via 28, 3a planta, 28013 Madrid, Espana", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 7, "   (Atencion presencial con cita previa)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Modalidad de trabajo:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "   Presencial (Madrid) y remoto (toda Espana)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.body_text(
        "Para solicitar una primera reunion de diagnostico gratuita de 45 minutos, puedes enviar un "
        "correo a contacto@demobusiness.ai con el asunto 'Reunion diagnostico' indicando brevemente "
        "el reto o proceso que quieres automatizar y el tamano de tu empresa. Te responderemos en "
        "menos de 24 horas laborables para coordinar una videollamada o reunion presencial en Madrid."
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 6,
        "Documento generado automaticamente | Demo Business S.L. | CIF B-12345678 | Version 1.0 | 2024",
        align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT
    )

    return pdf


def main():
    output_path = Path("static/uploads/knowledge/+34600000001/demo_business_knowledge.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = build_pdf()
    pdf.output(str(output_path))

    abs_path = output_path.resolve()
    print(f"PDF generado correctamente en: {abs_path}")
    print(f"Numero de paginas: {pdf.page}")


if __name__ == "__main__":
    main()
