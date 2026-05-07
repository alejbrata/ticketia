"""
seed_all.py — Reset completo + carga de datos demo para Demo Business S.L.

Ejecutar desde el contenedor:
    docker compose exec web python seed_all.py

O localmente desde TICKETIA_PRO/:
    python seed_all.py

Pasos que ejecuta en orden:
  1. Elimina y recrea todas las tablas (BD limpia)
  2. Crea el usuario demo con plan PRO_FULL
  3. Configura el wizard IA (sector, tono, FAQ, garantías, etc.)
  4. Indexa el conocimiento del wizard en pgvector (7 chunks)
  5. Genera el PDF de knowledge base (9 páginas)
  6. Ingesta el PDF en pgvector (18 chunks)
  7. Carga 15 tickets de historial de gastos
"""
import os
import sys

# ── Configuración ──────────────────────────────────────────────────────────────
DEMO_PHONE    = os.environ.get("DEMO_PHONE",         "+34600000001")
DEMO_EMAIL    = os.environ.get("DEMO_EMAIL",         "admin@demo.com")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD",      "demo1234")
DEMO_BUSINESS = os.environ.get("DEMO_BUSINESS_NAME", "Demo Business S.L.")


def step(n, label):
    print(f"\n[{n}/7] {label}")


def run():
    from app import app
    from core.db_models import db, BusinessProfile
    from werkzeug.security import generate_password_hash

    with app.app_context():

        # ── 1. Reset BD ────────────────────────────────────────────────────────
        step(1, "Limpiando base de datos...")
        db.drop_all()
        db.create_all()
        print("     OK")

        # ── 2. Crear usuario demo ──────────────────────────────────────────────
        step(2, f"Creando usuario: {DEMO_EMAIL}")
        user = BusinessProfile(
            user_phone=DEMO_PHONE,
            email=DEMO_EMAIL,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            business_name=DEMO_BUSINESS,
            plan_tier='PRO_FULL',
            features={"tickets_allowed": True, "bot_enabled": True, "dashboard_access": True},
            active_agents=[
                "grant_hunter", "networker", "business_health",
                "admin_redactor", "post_sales_service",
            ],
            agent_config={"post_sales_service": {"enable_feedback": False, "enable_reactivation": True}},
        )
        db.session.add(user)
        db.session.commit()
        print(f"     OK — login: {DEMO_EMAIL} / {DEMO_PASSWORD}")

        # ── 3. Configurar wizard IA ────────────────────────────────────────────
        step(3, "Configurando wizard IA (sector, tono, FAQ, garantias...)")
        import seed_wizard_config as wiz
        wiz.DEMO_PHONE = DEMO_PHONE
        wiz.seed()

        # ── 4. (ya hecho dentro de seed_wizard_config → ingest_wizard_chunks) ──
        # seed_wizard_config.seed() ya indexa los 7 chunks del wizard en pgvector

        # ── 5. Generar PDF knowledge base ──────────────────────────────────────
        step(5, "Generando PDF de knowledge base (9 paginas)...")
        import seed_knowledge_pdf as kpdf
        # Redirigir la ruta de salida al usuario demo correcto
        from pathlib import Path
        pdf_dir = Path(f"static/uploads/knowledge/{DEMO_PHONE}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / "demo_business_knowledge.pdf"
        kpdf.OUTPUT_PATH = pdf_path
        kpdf.main()

        # ── 6. Ingestar PDF en pgvector ────────────────────────────────────────
        step(6, "Indexando PDF en pgvector...")
        from modules.services.embeddings import ingest_document
        chunks = ingest_document(DEMO_PHONE, str(pdf_path), "demo_business_knowledge.pdf")
        print(f"     OK — {chunks} chunks indexados")

        # ── 7. Tickets de historial ────────────────────────────────────────────
        step(7, "Cargando 15 tickets de historial de gastos...")
        import seed_demo
        seed_demo.generate_fake_history(DEMO_PHONE)
        print("     OK")

    print("\n" + "="*50)
    print("Demo lista.")
    print(f"  URL      : http://localhost:5000")
    print(f"  Email    : {DEMO_EMAIL}")
    print(f"  Password : {DEMO_PASSWORD}")
    print(f"  Chunks RAG: wizard(7) + PDF(18) = 25 total")
    print("="*50)


if __name__ == "__main__":
    run()
