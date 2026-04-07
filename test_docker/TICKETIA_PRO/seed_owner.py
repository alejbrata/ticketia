from app import app
from core.db_models import db, BusinessProfile
from werkzeug.security import generate_password_hash

# Configuración del Dueño
MI_TELEFONO = "+34630339601"
NOMBRE_NEGOCIO = "Mi Empresa S.L."

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
                email="admin@ticketia.com",
                password_hash=generate_password_hash("1234"),
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
