from app import app
from core.db_models import db, BusinessProfile
from werkzeug.security import generate_password_hash
import os

# Configuración del usuario demo
# Personaliza estas variables o pásalas por entorno
MI_TELEFONO = os.environ.get("DEMO_PHONE", "+34600000001")
NOMBRE_NEGOCIO = os.environ.get("DEMO_BUSINESS_NAME", "Demo Business S.L.")

def seed():
    with app.app_context():
        print(f"🌱 Conectando a Base de Datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # 1. Crear Tablas
        print("🛠️  Creando tablas...")
        db.create_all()
        
        # 2. Verificar/Crear Usuario
        print(f"👤 Verificando usuario: {MI_TELEFONO}...")
        existing_user = BusinessProfile.query.filter_by(user_phone=MI_TELEFONO).first()
        
        if not existing_user:
            print("   - Usuario no existe. Creando...")
            new_profile = BusinessProfile(
                user_phone=MI_TELEFONO,
                email=os.environ.get("DEMO_EMAIL", "admin@demo.com"),
                password_hash=generate_password_hash(os.environ.get("DEMO_PASSWORD", "demo1234")),
                business_name=NOMBRE_NEGOCIO,
                plan_tier='PRO_FULL',
                features={"tickets_allowed": True, "bot_enabled": True, "dashboard_access": True}
            )
            db.session.add(new_profile)
            db.session.commit()
            print("✅ Usuario Admin Creado (Pass: 1234)")
        else:
            print("ℹ️  El usuario ya existe.")

        print("✅ Base de datos inicializada correctamente.")

if __name__ == "__main__":
    seed()
