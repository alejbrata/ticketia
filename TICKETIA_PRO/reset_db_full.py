from app import app
from core.db_models import db, BusinessProfile
from werkzeug.security import generate_password_hash

# Configuración del Dueño
MI_TELEFONO = "+34630339601"
NOMBRE_NEGOCIO = "Mi Empresa S.L."

def reset_and_seed():
    with app.app_context():
        print(f"🔥 RESETEANDO Base de Datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # 1. Borrar Todo
        print("🗑️  Borrando tablas existentes...")
        db.drop_all()
        
        # 2. Crear Todo
        print("🛠️  Re-creando tablas...")
        db.create_all()
        
        # 3. Crear Usuario Admin
        print(f"👤 Creando usuario Admin: {MI_TELEFONO}...")
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
        
        print("✅ ¡Base de datos limpia y Usuario Admin restaurado!")
        print("   - User: +34630339601")
        print("   - Pass: 1234")

if __name__ == "__main__":
    reset_and_seed()
