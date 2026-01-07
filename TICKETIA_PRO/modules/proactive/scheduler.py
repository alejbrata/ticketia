from core.db_models import BusinessProfile

# Importamos los agentes (Skeletons)
from modules.proactive.grant_hunter import GrantHunterAgent
from modules.proactive.networker import SynergyAgent
from modules.proactive.business_health import BusinessCoachAgent
from modules.proactive.admin_redactor import AdminAssistantAgent
from modules.proactive.invoice_reclaimer import ReclaimerAgent

def run_daily_tasks():
    """
    Punto de entrada para el 'Cron Job' diario.
    Esta función debería ser invocada por un scheduler externo (ej: Celery, APScheduler)
    o un trigger temporal simple en la app principal.
    """
    print("⏰ Ejecutando Tareas Proactivas Diarias...")
    
    # 1. Recuperar usuarios activos
    # Ahora sí consultamos la DB real
    users = BusinessProfile.query.all()
    
    for user in users:
        try:
            # Lista de agentes contratados por este usuario (JSON field)
            # Aseguramos que sea una lista (default [])
            active_list = user.active_agents or []
            
            print(f"🔄 Procesando usuario {user.business_name} (Activos: {active_list})")
            
            # A) Chequeo de Subvenciones
            if "grant_hunter" in active_list:
                # grant_hunter = GrantHunterAgent()
                # opportunities = grant_hunter.check_new_grants(user)
                # ...
                print("   -> Ejecutando Grant Hunter...")
            
            # B) Análisis de Salud Financiera
            if "business_health" in active_list:
                # coach = BusinessCoachAgent()
                # ...
                print("   -> Ejecutando Business Coach...")
            
            # C) Networking
            if "networker" in active_list:
                 # ...
                 print("   -> Ejecutando Networker...")
                 
            # D) Admin Assistant
            if "admin_redactor" in active_list:
                # ...
                print("   -> Ejecutando Admin Assistant...")
            
            # E) Invoice Reclaimer
            if "invoice_reclaimer" in active_list:
                # ...
                print("   -> Ejecutando Invoice Reclaimer...")
            
        except Exception as e:
            print(f"Error procesando tareas para usuario {user.id}: {e}")
            
    print("✅ Tareas Proactivas Finalizadas.")
