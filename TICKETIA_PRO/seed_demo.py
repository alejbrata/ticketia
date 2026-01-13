import random
from datetime import datetime, timedelta
from app import app
from core.db_models import db, Ticket

def generate_fake_history(phone):
    with app.app_context():
        # Generar tickets mes pasado
        today = datetime.now()
        last_month = today - timedelta(days=30)
        providers = ["Amazon", "Gasolinera LowCost", "Restaurante Paco", "Apple Store", "Uber"]
        
        for _ in range(15):
            t = Ticket(
                user_phone=phone, status='processed',
                concept="Gasto Demo", total=round(random.uniform(15, 120), 2),
                date=last_month.replace(day=random.randint(1, 28)),
                provider=random.choice(providers),
                image_path="https://placehold.co/400"
            )
            db.session.add(t)
        db.session.commit()
