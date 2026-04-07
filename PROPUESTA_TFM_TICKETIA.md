# Propuesta de Proyecto de TFM: Ticketia (Zeptai)

**Título propuesto:** Ticketia: Plataforma de Gestión Financiera y Asesoramiento Estratégico para Pymes basada en Sistemas Multiagente con IA Generativa.

---

## 1. Descripción de la propuesta

El proyecto consiste en el diseño y desarrollo de un **Producto Mínimo Viable (MVP)** de una aplicación web, denominada "Ticketia", orientada a automatizar la administración financiera y proporcionar consultoría y soporte a pymes y trabajadores autónomos.

La solución está desarrollada íntegramente en **Python** y tiene como pilar fundamental el uso avanzado de la **Inteligencia Artificial Generativa**, alejándose de los chatbots conversacionales simples para implementar una arquitectura de **Agentes Autónomos y Sistemas Multiagente (MAS)**.

El MVP acota su alcance a las siguientes funcionalidades clave, demostrando la versatilidad de la IA:
*   **Procesamiento Inteligente de Gastos:** Un módulo de visión artificial y NLP basado en LLMs que permite subir imágenes de tickets/facturas o notas de voz. La IA extrae de forma estructurada los datos y los registra automáticamente.
*   **"El Consejo" (Multi-Agent Debate System):** El núcleo innovador estratégico. Una sala de juntas virtual donde el usuario plantea dilemas empresariales, y múltiples agentes de IA especializados (Legal, Financiero, Marketing) debaten entre sí. Los agentes razonan y entregan una resolución consensuada.
*   **Agente de Postventa Autónomo:** Un asistente conversacional especializado en gestionar solicitudes de cambio, devoluciones y quejas de forma empática y resolutiva, siendo configurable según las políticas de cada negocio.
*   **Business Coach (Alertas Proactivas):** Un planificador en segundo plano que analiza diariamente el estado financiero. Actúa de forma proactiva enviando notificaciones push al usuario si detecta anomalías o desviaciones presupuestarias.
*   **Generación de Contenido Multimedia:** Integración de capacidades de IA generativa de vanguardia para la creación de vídeos a partir de imágenes estáticas, explorando el caso de uso de soporte en marketing digital para la pyme.
*   **Integración de Herramientas (Tool Use / MCP):** Los agentes emplean LLMOps para ejecutar acciones reales: buscar normativas en internet en tiempo real (ej. BOE) o generar documentos descargables (PDF/Excel) de manera autónoma.

La plataforma se expone mediante una interfaz web interactiva tipo PWA (aplicación web progresiva) y se despliega encapsulada en **Docker**.

---

## 2. Motivaciones de la misma

La motivación principal para este desarrollo nace de una necesidad real en el tejido empresarial: los autónomos y las microempresas carecen del tiempo para la gestión administrativa y de los recursos económicos para contratar un comité asesor.

A nivel académico, este proyecto está motivado por la necesidad de aplicar de forma práctica y transversal los conocimientos adquiridos en el máster. El proyecto justifica integralmente la asimilación del programa formativo mediante las siguientes aplicaciones:
*   **Modelos generativos de imagen, audio y vídeo (Tema 6) y LLMs (Tema 4):** Utilizados para el procesamiento multimodal de tickets (OCR/Visión), transcripción de notas de voz y la futura generación de vídeos de marketing.
*   **ReAct prompting, desarrollo de agentes y automatización (Tema 12):** Fundamental para orquestar "El Consejo", el agente de Postventa y el planificador proactivo del Business Coach.
*   **APIs, MCP, Integración y MLOps (Tema 8):** Implementado mediante la conexión del orquestador a servidores Model Context Protocol para buscar en el BOE y la dotación de "Tool Use" a los agentes (generación Excel).
*   **Desarrollo de aplicaciones y POCs (Tema 11) con Frameworks populares (Tema 10):** Creación del producto completo utilizando Python, APIs de back-end y Frontend interactivo para asegurar la entrega de un MVP real.
*   **Cloud e infraestructura (Tema 9):** Encapsulación y despliegue del MVP funcional mediante contenedores Docker.

---

## 3. Objetivos finales que se persiguen

El **Objetivo Principal** del proyecto es desarrollar e implantar un Producto Mínimo Viable (MVP) demostrable de un asistente virtual integral para pymes, utilizando Python y un marco de trabajo basado en sistemas de IA Generativa avanzada.

Para asegurar que este objetivo sea medible y acotado al tiempo disponible, se establecen los siguientes **Objetivos Secundarios alineados con el temario del máster**:

1.  **Automatización Multimodal en Entrada y Salida (Ref. Temas 4 y 6):** Implementar un pipeline que extraiga datos financieros de recibos (audio/imagen) superando un 85% de precisión, y desarrollar un módulo que verifique la viabilidad de la generación de contenido audiovisual (vídeo a partir de imágenes estáticas) para propósitos de marketing.
2.  **Desarrollo de orquestación Multiagente ReAct ("El Consejo") (Ref. Tema 12):** Diseñar y programar la lógica algorítmica donde múltiples perfiles de IA interactúen entre sí, encadenen razonamientos y lleguen a un consejo estratégico unificado sin entrar en bucles de alucinación.
3.  **Implementación de Agentes Especializados y Proactivos (Ref. Temas 11 y 12):** Desarrollar un "Agente de Postventa" capaz de interactuar con clientes de la pyme y resolver quejas basándose en políticas dinámicas (reactivo) y un "Business Coach" que audite las finanzas en segundo plano y alerte al usuario sobre desviaciones de gastos (proactivo y automatizado).
4.  **Integración de herramientas (Tool Use / MCP) y Despliegue (Ref. Temas 8 y 9):** Dotar a los agentes de la capacidad de invocar funciones Python externas a través de Model Context Protocol (búsquedas MCP en internet para leyes actualizadas del BOE, generación de Excel), y construir un dashboard PWA funcional, contenerizando toda la solución.
