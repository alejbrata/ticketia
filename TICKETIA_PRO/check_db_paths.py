from app import app
from core.db_models import Ticket

with app.app_context():
    tickets = Ticket.query.order_by(Ticket.id.desc()).limit(5).all()
    print("-" * 50)
    print(f"{'ID':<5} | {'Date':<12} | {'Image Path'}")
    print("-" * 50)
    for t in tickets:
        print(f"{t.id:<5} | {t.date.strftime('%d/%m') if t.date else 'N/A':<12} | {t.image_path}")
    print("-" * 50)
