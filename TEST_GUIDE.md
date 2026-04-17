# Guía de Pruebas — Zeptai / Ticketia PRO

> **Entorno:** Docker local → http://localhost:5000  
> **Orden recomendado:** de arriba a abajo. Cada sección indica si necesita datos previos.

---

## 0. Preparación inicial

### 0.1 Registro y Login
1. Acceder a `/register` y crear un usuario nuevo.
2. Completar el **Wizard de onboarding** (`/wizard`) con:
   - Nombre del negocio, sector, descripción de servicios.
   - Cuantos más datos, mejor funcionará el Networker y el Coach.
3. Verificar redirección al dashboard tras completar.

### 0.2 Seed de demo (datos base)
Desde el panel Demo (`/demo`) o ejecutando en la consola del contenedor:

```bash
docker exec -it ticketia_app python -c "
from app import app
from routes.web import _seed_demo_data_for_user
with app.app_context():
    _seed_demo_data_for_user('+34XXXXXXXXX')  # tu teléfono de prueba
"
```

Esto inserta **10 tickets históricos** y una **notificación de bienvenida**.

### 0.3 Base de Conocimiento RAG (pgvector) — cargar antes de la demo

Para que el asistente responda con datos reales de la empresa es necesario indexar al menos un documento.

**Archivo listo para usar:** `ialex_solutions_knowledge_base.pdf` (raíz del repositorio)

**Pasos:**
1. Entra en la app y ve a **Menú lateral → 📚 Base de Conocimiento** o abre [http://localhost:5000/knowledge](http://localhost:5000/knowledge).
2. Arrastra `ialex_solutions_knowledge_base.pdf` sobre la zona de subida (o pulsa para seleccionarlo).
3. Pulsa **"Procesar e indexar"** — los embeddings se generan en segundo plano con `text-embedding-3-small`.
4. Cuando el documento aparezca en la lista, el RAG está activo.

**Verificar que funciona** — prueba en el chat:

| Pregunta | Respuesta esperada |
|---|---|
| `"¿Cuánto cuesta implantar un agente IA?"` | Tarifas del catálogo (Starter 2.500 €, Business 6.000 €…) |
| `"¿Tenéis demo gratuita?"` | Demo personalizada de 45 min, contacto hola@ialex-solutions.com |
| `"¿Qué modelos de IA usáis?"` | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro |
| `"¿Cuál es el email de soporte?"` | soporte@ialex-solutions.com |

> **Cómo funciona:** el PDF se trocea en fragmentos de ~400 caracteres, cada uno se convierte en un vector de 1.536 dimensiones almacenado en PostgreSQL con la extensión `pgvector`. Al llegar una pregunta al chat, se recuperan los 5 fragmentos más similares por distancia coseno y se inyectan en el contexto del LLM antes de generar la respuesta.

### 0.4 Datos sintéticos adicionales ⚠️
> Algunas funcionalidades necesitan datos que el seed de demo **no genera**.  
> Ver sección [Apéndice: Script de datos sintéticos](#apéndice-script-de-datos-sintéticos).

---

## 1. Tickets

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Ir a la sección de Tickets | Listado de tickets del seed visible |
| 2 | Crear ticket manual (proveedor, importe, concepto) | Aparece en listado con estado `processed` |
| 3 | Subir imagen de ticket (foto/factura) | Se procesa con OCR y extrae datos automáticamente |
| 4 | Verificar cálculo de base imponible e IVA | `base = total / 1.21` al 21% |

---

## 2. Generación de presupuestos

> **Datos necesarios:** ninguno extra.  
> **Canal:** chat (widget 💬 en cualquier página).

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Abrir chat y pedir: *"Genera un presupuesto para [cliente] con [partidas]"* | El agente llama a `create_proposal_from_text` |
| 2 | Esperar confirmación en el chat | Mensaje "Se ha generado el documento..." |
| 3 | **Campanita** 🔔 | Badge rojo aparece en ≤ 15 segundos SIN abrir el drawer |
| 4 | Abrir notificaciones | Aparece "📄 Presupuesto listo" con enlace a Documentos |
| 5 | Ir a `/documents` | PDF listado y descargable |

---

## 3. Imagen (marketing)

> **Datos necesarios:** ninguno extra.  
> **Canal:** chat o página `/marketing`.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Chat: *"Genera una imagen de [descripción]"* | Respuesta inmediata "⏳ me pongo a ello..." |
| 2 | Esperar ~30s | **Campanita** se ilumina sola |
| 3 | Abrir notificaciones | "🖼️ Imagen lista" con enlace a Documentos |
| 4 | Ir a `/documents` → Imágenes | Imagen visible y descargable |

---

## 4. Vídeo / Reel

> **Requiere:** `RUNWAYML_API_SECRET` configurado en `.env`.  
> **Canal:** chat o página `/marketing`.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Chat: *"Genera un reel de [tema]"* | Respuesta "⏳" inmediata |
| 2 | Esperar generación (puede tardar 1-2 min) | **Campanita** se ilumina |
| 3 | Abrir notificaciones | "🎬 Reel listo" |
| 4 | Ir a `/documents` → Video Prompts | Fichero listado |

> Si no hay clave de Runway, el sistema notifica el error con "⚠️ Error generando vídeo".

---

## 5. Presentación (PPT)

> **Canal:** chat.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Chat: *"Crea una presentación sobre [tema]"* | Respuesta "⏳" |
| 2 | Esperar generación | **Campanita** se ilumina |
| 3 | Notificación "📊 Presentación lista" | Enlace a Documentos |
| 4 | Descargar `.pptx` | Fichero abre correctamente en PowerPoint/Impress |

---

## 6. Admin Redactor multimodal (imagen → presupuesto)

> **Diferente al flujo de texto.** Usa visión por computador sobre la imagen.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Subir foto de un ticket/albarán en el chat | Se detecta como imagen |
| 2 | El agente la procesa automáticamente (si `admin_redactor` activo) | PDF generado |
| 3 | Alternativamente: *"Genera presupuesto de mi última imagen"* | Llama a `create_proposal_from_last_image` |
| 4 | **Campanita** se ilumina | Notificación "📄 Presupuesto listo" |

---

## 7. Calendario

> **Datos necesarios:** ⚠️ Arranca vacío. Ver script en el apéndice para precargar citas.  
> **Canal:** chat.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Chat: *"¿Hay disponibilidad el [fecha]?"* | Llama a `check_availability`, devuelve huecos libres |
| 2 | Chat: *"Reserva cita para [nombre] el [fecha] a las [hora]"* | Llama a `book_appointment`, confirma reserva |
| 3 | Repetir con misma hora | El agente informa que ya está ocupada |

---

## 8. Consejo de Agentes

> **Datos necesarios:** ninguno.  
> **Página:** `/council`

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Introducir un dilema de negocio | Ej: *"¿Debo subir precios un 15%?"* |
| 2 | Observar Ronda 1 | Los 3 agentes (Socio 🐯, Gestor 🦉, Coach 🚀) opinan en streaming |
| 3 | Observar Ronda 2 (Debate) | Cada agente replica a los otros |
| 4 | Observar Ronda 3 (Síntesis) | El Secretario 📝 genera un plan de acción |
| 5 | Verificar que el "Plan de Acción" es coherente con el dilema | — |

---

## 9. Chat conversacional general

> Flujo base sin herramientas especiales.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Preguntar algo sobre el negocio: *"¿Cuánto he gastado este mes?"* | Respuesta coherente usando historial de tickets |
| 2 | Pregunta de contexto: *"¿Cuál es mi sector?"* | Usa `static_knowledge` del perfil |
| 3 | Abrir chat, cerrar, volver a abrir | El historial de la sesión se mantiene |

---

## 10. Post-Ventas

> **Datos necesarios:** ⚠️ Requiere `agent_config` configurado. Ver apéndice.  
> **Canal:** chat (activa el agente `PostSalesAgent`).

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Chat: *"Quiero devolver un producto"* | El agente explica la política de cambios |
| 2 | Chat: *"Me llegó el pedido dañado, estoy muy enfadado"* | El sistema detecta cliente enfadado, crea `Incident` en BD |
| 3 | **Campanita** | Notificación "🚨 CLIENTE ENFADADO" o "⚠️ Solicitud de Devolución" |
| 4 | Abrir notificaciones | Alerta visible con tipo `alert` (fondo rojo) |

---

## 11. Demo — Agente BOE (Grant Hunter)

> **Datos necesarios:** grants en BD. Se crean con el botón "Seed Grants" del panel demo.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Panel Demo → "Seed Grants" (si no se hizo antes) | 3 grants insertados en BD |
| 2 | Panel Demo → "Lanzar Grant Hunter" | El agente compara el sector del usuario con los grants |
| 3 | **Campanita** | Notificación "💰 Nueva Ayuda Disponible" |
| 4 | Abrir notificación | Enlace con detalle de la subvención |

---

## 12. Demo — Agente de Salud Financiera (Business Coach)

> **Datos necesarios:** ⚠️ Necesita tickets en **mes pasado** Y **mes actual** con importes.  
> El seed de demo inserta 10 tickets de los últimos 60 días, pero sin control temporal preciso.  
> Para un resultado fiable, usar el script del apéndice.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Panel Demo → "Lanzar Business Coach" | El agente calcula stats mensuales |
| 2 | **Campanita** | Notificación con resumen diario y % de variación |
| 3 | Notificación incluye 📈 o 📉 según tendencia | — |
| 4 | Si proyección > 20% de variación | Se dispara alerta automática |

---

## 13. Demo — Networker Agent

> **Datos necesarios:** ⚠️ Requiere **mínimo 2 usuarios** con `static_knowledge` completado.  
> El seed de demo NO crea usuarios adicionales. Ver apéndice.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Crear 2 usuarios con sectores complementarios (ver apéndice) | — |
| 2 | Panel Demo → "Lanzar Networker" | El agente evalúa synergy score entre usuarios |
| 3 | Si score ≥ 80 | **Campanita** con "🤝 Nueva Oportunidad de Negocio" |
| 4 | Notificación con `SynergyMatch` guardado en BD | — |

---

## 14. Documentos

> Verifica que todos los documentos generados en los pasos anteriores aparecen.

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Ir a `/documents` | Listado de `GeneratedDocument` del usuario |
| 2 | Filtrar por categoría (Propuestas / Imágenes / Presentaciones / Vídeos) | Categorización correcta |
| 3 | Pulsar descarga en cada tipo | Fichero descarga sin error 404 |

---

## 15. Notificaciones (verificación completa)

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Generar un presupuesto desde chat | Badge rojo aparece en ≤ 15s sin interacción |
| 2 | Abrir drawer (campanita) | Lista de notificaciones cargada |
| 3 | Marcar una como leída | Desaparece el botón "Marcar leído", opacidad reducida |
| 4 | "Marcar todas leídas" | Badge desaparece, toast "Todo marcado como leído ✅" |
| 5 | Cerrar drawer y esperar | Badge no reaparece si no hay nuevas |

---

## 16. Métricas

> **Datos necesarios:** LLMCall registrados automáticamente al usar el chat.  
> Probar **después** de haber hecho los pasos anteriores (mínimo 5-10 interacciones de chat).

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Ir a `/metrics` | Gráficas de tokens, coste y latencia |
| 2 | Verificar desglose por `stage` | chat_main, chat_tool_followup, council_opinion, etc. |
| 3 | Verificar desglose por modelo | gpt-4o |
| 4 | Comprobar serie temporal (últimos 14 días) | Puntos en el eje X desde el inicio de pruebas |

---

## 17. Perfil

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Ir a `/profile` o Wizard | Formulario con datos actuales |
| 2 | Cambiar sector o descripción de servicios | Se guarda en `static_knowledge` |
| 3 | Volver al chat y preguntar por el sector | El agente refleja el cambio |
| 4 | Subir logo | Aparece en documentos generados posteriormente |

---

## 18. PWA (bonus — desde móvil o Chrome)

| Paso | Acción | Resultado esperado |
|------|--------|--------------------|
| 1 | Abrir desde Chrome en Android o iOS | Banner "Instalar Zeptai" aparece |
| 2 | Instalar | App se abre en modo standalone sin barra del navegador |
| 3 | Activar notificaciones push (si hay VAPID keys) | Toast "Notificaciones push activadas 🔔" |

---

## Apéndice: Script de datos sintéticos

Para los agentes que lo requieren (Networker, Post-Sales, Calendar, Business Coach), ejecutar desde la raíz del proyecto:

```bash
docker exec -it ticketia_app python /app/TICKETIA_PRO/seed_test_data.py
```

O crear el fichero `TICKETIA_PRO/seed_test_data.py` con el siguiente contenido:

```python
"""
Genera datos sintéticos para completar las pruebas de:
- Networker Agent (2 usuarios extra con sectores complementarios)
- Post-Sales (agent_config en el usuario principal)
- Calendar (3 citas futuras)
- Business Coach (tickets con fechas de mes pasado y mes actual)

USO: docker exec -it ticketia_app python /app/TICKETIA_PRO/seed_test_data.py
"""
import sys, os
sys.path.insert(0, '/app/TICKETIA_PRO')
os.chdir('/app/TICKETIA_PRO')

from app import app
from core.db_models import db, BusinessProfile, Ticket, Appointment
from datetime import datetime, timedelta
import random

MAIN_USER_PHONE = "+34XXXXXXXXX"  # ← Cambiar por tu teléfono de prueba


def seed_networker():
    """2 usuarios con sectores complementarios al usuario principal."""
    if BusinessProfile.query.filter_by(user_phone="+34600000001").first():
        print("  Networker: usuarios ya existen, omitido.")
        return

    u1 = BusinessProfile(
        user_phone="+34600000001",
        email="proveedor1@test.es",
        business_name="Distribuciones García",
        static_knowledge={"sector": "Distribución", "services": "Suministro mayorista a tiendas"},
        active_agents=[]
    )
    u2 = BusinessProfile(
        user_phone="+34600000002",
        email="logistica2@test.es",
        business_name="Logística Rápida SL",
        static_knowledge={"sector": "Logística", "services": "Transporte y almacenamiento"},
        active_agents=[]
    )
    db.session.add_all([u1, u2])

    # Tickets del usuario principal que referencian a estos proveedores
    for i in range(5):
        t = Ticket(
            user_phone=MAIN_USER_PHONE,
            provider="Distribuciones García" if i < 3 else "Logística Rápida SL",
            total=round(random.uniform(150, 600), 2),
            concept="Suministro mensual" if i < 3 else "Portes",
            date=datetime.now() - timedelta(days=random.randint(3, 25)),
            status="processed",
            tax_percent=21
        )
        db.session.add(t)

    db.session.commit()
    print("  Networker: 2 usuarios y 5 tickets creados.")


def seed_post_sales():
    """Configura agent_config con política de devoluciones."""
    user = BusinessProfile.query.filter_by(user_phone=MAIN_USER_PHONE).first()
    if not user:
        print("  Post-Sales: usuario principal no encontrado.")
        return

    config = user.agent_config or {}
    if "post_sales" in config:
        print("  Post-Sales: ya configurado, omitido.")
        return

    config["post_sales"] = {
        "forbidden_items": ["medicamentos", "alimentos perecederos"],
        "allow_refunds": True,
        "exchange_policy": {
            "url": "https://mitienda.com/cambios",
            "instructions": "Contacta con soporte en 48h indicando nº de pedido."
        }
    }
    user.agent_config = config
    db.session.commit()
    print("  Post-Sales: agent_config configurado.")


def seed_calendar():
    """3 citas en los próximos 3 días."""
    user = BusinessProfile.query.filter_by(user_phone=MAIN_USER_PHONE).first()
    if not user:
        print("  Calendar: usuario principal no encontrado.")
        return

    existing = Appointment.query.filter_by(business_phone=MAIN_USER_PHONE).count()
    if existing >= 3:
        print("  Calendar: citas ya existen, omitido.")
        return

    slots = [("09:00", "Ana Martínez"), ("11:00", "Carlos López"), ("16:00", "Elena Ruiz")]
    for i, (hour, name) in enumerate(slots):
        appt = Appointment(
            business_phone=MAIN_USER_PHONE,
            date=(datetime.now() + timedelta(days=i + 1)).date(),
            time=hour,
            client_name=name,
            client_phone=f"+3460000{i:04d}"
        )
        db.session.add(appt)

    db.session.commit()
    print("  Calendar: 3 citas creadas.")


def seed_business_coach():
    """Tickets de mes pasado (1000€) y mes actual (1500€) para análisis de tendencia."""
    user = BusinessProfile.query.filter_by(user_phone=MAIN_USER_PHONE).first()
    if not user:
        print("  Business Coach: usuario principal no encontrado.")
        return

    today = datetime.now()
    first_this_month = today.replace(day=1)
    last_month_date = first_this_month - timedelta(days=15)

    # Evitar duplicados
    existing = Ticket.query.filter_by(user_phone=MAIN_USER_PHONE, concept="[TEST] Gasto mes pasado").first()
    if existing:
        print("  Business Coach: datos ya existen, omitido.")
        return

    t_last = Ticket(
        user_phone=MAIN_USER_PHONE,
        provider="Proveedor Test",
        total=1000.0,
        base=826.45,
        tax_percent=21,
        concept="[TEST] Gasto mes pasado",
        date=last_month_date,
        status="processed"
    )
    t_curr = Ticket(
        user_phone=MAIN_USER_PHONE,
        provider="Proveedor Test",
        total=1500.0,
        base=1239.67,
        tax_percent=21,
        concept="[TEST] Gasto mes actual",
        date=today,
        status="processed"
    )
    db.session.add_all([t_last, t_curr])
    db.session.commit()
    print("  Business Coach: tickets de mes pasado y actual creados (+50% variación).")


if __name__ == "__main__":
    print(f"\nGenerando datos sintéticos para usuario: {MAIN_USER_PHONE}\n")
    with app.app_context():
        seed_networker()
        seed_post_sales()
        seed_calendar()
        seed_business_coach()
    print("\n✅ Listo. Ahora ejecuta los demos desde el panel /demo.\n")
```

> **Importante:** edita `MAIN_USER_PHONE` con el teléfono del usuario de prueba antes de ejecutar.

---

## Resumen de cobertura

| Funcionalidad | Seed demo | Script extra | Sin datos previos |
|---|:---:|:---:|:---:|
| Tickets | ✅ | — | — |
| Presupuesto (texto) | — | — | ✅ |
| Presupuesto (imagen) | — | — | ✅ |
| Imagen marketing | — | — | ✅ |
| Vídeo / Reel | — | — | ✅ |
| PPT | — | — | ✅ |
| Admin Redactor | — | — | ✅ |
| Chat general | — | — | ✅ |
| Calendario | — | ✅ | — |
| Consejo de Agentes | — | — | ✅ |
| Post-Ventas | — | ✅ | — |
| Grant Hunter (BOE) | ✅ | — | — |
| Business Coach | ✅ (parcial) | ✅ (exacto) | — |
| Networker | — | ✅ | — |
| Documentos | — | — | ✅ (tras generar) |
| Notificaciones | ✅ | — | — |
| Métricas | — | — | ✅ (tras usar chat) |
| Perfil / Wizard | — | — | ✅ |
