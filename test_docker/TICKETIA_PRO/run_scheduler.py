from app import app
from modules.proactive.scheduler import run_daily_tasks
import schedule
import time
from datetime import datetime

def job():
    print(f"⏰ Ejecutando Tareas Programadas: {datetime.now()}")
    with app.app_context():
        run_daily_tasks()

if __name__ == "__main__":
    print("🚀 Scheduler Activo (Modo Persistente)")
    print("   - Ejecución inmediata para prueba.")
    print("   - Programado diariamente a las 09:00 AM.")
    
    # 1. Ejecución Inmediata (para que veas que funciona ya)
    job()
    
    # 2. Programación Recurrente
    schedule.every().day.at("09:00").do(job)
    
    # 3. Bucle Infinito
    while True:
        schedule.run_pending()
        time.sleep(60)
