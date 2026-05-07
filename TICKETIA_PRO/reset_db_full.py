import os
from app import app
from core.db_models import db, BusinessProfile
from werkzeug.security import generate_password_hash

DEMO_PHONE    = os.environ.get("DEMO_PHONE",         "+34600000001")
DEMO_EMAIL    = os.environ.get("DEMO_EMAIL",         "admin@demo.com")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD",      "demo1234")
DEMO_BUSINESS = os.environ.get("DEMO_BUSINESS_NAME", "Demo Business S.L.")

def reset_and_seed():
    with app.app_context():
        print(f"[reset] DB: {app.config['SQLALCHEMY_DATABASE_URI']}")

        db.drop_all()
        print("[reset] Tablas eliminadas.")

        db.create_all()
        print("[reset] Tablas recreadas.")

        new_profile = BusinessProfile(
            user_phone=DEMO_PHONE,
            email=DEMO_EMAIL,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            business_name=DEMO_BUSINESS,
            plan_tier='PRO_FULL',
            features={"tickets_allowed": True, "bot_enabled": True, "dashboard_access": True},
            active_agents=["grant_hunter", "networker", "business_health", "admin_redactor", "post_sales_service"],
            agent_config={
                "post_sales_service": {
                    "enable_feedback": False,
                    "enable_reactivation": True,
                }
            }
        )
        db.session.add(new_profile)
        db.session.commit()

        print(f"[reset] Usuario creado: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print("[reset] Listo. BD limpia y lista para prueba.")

if __name__ == "__main__":
    reset_and_seed()
