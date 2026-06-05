from app import app
from core.db_models import db, BusinessProfile

def seed_policy():
    with app.app_context():
        print("🛡️ Inyectando Políticas de Seguridad...")
        
        email = "admin@zeptai.com"
        user = BusinessProfile.query.filter_by(email=email).first()
        
        if user:
            # Configuración de Seguridad Post-Venta
            policy_config = {
                "post_sales": {
                    "forbidden_items": ["calzoncillos", "ropa interior", "pendientes", "bañador"],
                    "allow_autonomous_refunds": False,
                    "exchange_policy": {
                        "url": "https://zeptai.com/cambios-y-devoluciones",
                        "instructions": "Si prefieres, también puedes venir a nuestra tienda en C/ Gran Vía 12."
                    }
                }
            }
            
            # Merge with existing config if needed, or overwrite
            current_config = dict(user.agent_config) if user.agent_config else {}
            current_config.update(policy_config)
            
            # Re-assign to trigger tracking
            user.agent_config = current_config
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "agent_config")
            
            db.session.commit()
            print("✅ Política guardada en DB.")
            
            # Re-fetch to verify
            print(f"✅ Política aplicada a {user.business_name}:")
            print(f"   - Prohibido: {user.agent_config['post_sales']['forbidden_items']}")
            print(f"   - Auto-Reembolso: {user.agent_config['post_sales']['allow_autonomous_refunds']}")
        else:
            print("❌ No encontré al usuario admin.")

if __name__ == "__main__":
    seed_policy()
