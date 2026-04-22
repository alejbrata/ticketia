# -*- coding: utf-8 -*-
"""
reset_demo.py — Limpia todos los datos de demo de una cuenta para empezar de cero.
Uso:
    docker exec ticketia_app python reset_demo.py 630339601
"""
import sys
from app import app, db
from core.db_models import (
    Ticket, Appointment, ChatMessage, ActivityLog,
    SynergyMatch, Notification, GeneratedDocument,
    LLMCall, KnowledgeChunk, Incident, Grant
)

PARTNER_PHONE = 'demo_partner_tfm'

def reset(phone):
    with app.app_context():
        print(f"\n Limpiando datos de demo para: {phone}")
        print("-" * 45)

        # Tickets
        n = Ticket.query.filter_by(user_phone=phone).delete()
        print(f"  Tickets eliminados:           {n}")

        # Citas
        n = Appointment.query.filter_by(business_phone=phone).delete()
        print(f"  Citas eliminadas:             {n}")

        # Historial de chat
        n = ChatMessage.query.filter_by(user_phone=phone).delete()
        print(f"  Mensajes de chat eliminados:  {n}")

        # Activity log
        n = ActivityLog.query.filter_by(user_phone=phone).delete()
        print(f"  Registros de actividad:       {n}")

        # Notificaciones
        n = Notification.query.filter_by(user_phone=phone).delete()
        print(f"  Notificaciones eliminadas:    {n}")

        # Sinergias (como user_a o user_b)
        n = SynergyMatch.query.filter(
            (SynergyMatch.user_a_phone == phone) |
            (SynergyMatch.user_b_phone == phone)
        ).delete(synchronize_session=False)
        print(f"  Sinergias eliminadas:         {n}")

        # Empresa partner ficticia de demo
        n = SynergyMatch.query.filter(
            (SynergyMatch.user_a_phone == PARTNER_PHONE) |
            (SynergyMatch.user_b_phone == PARTNER_PHONE)
        ).delete(synchronize_session=False)
        from core.db_models import BusinessProfile
        partner = BusinessProfile.query.filter_by(user_phone=PARTNER_PHONE).first()
        if partner:
            db.session.delete(partner)
            print(f"  Empresa demo eliminada:       CreativaMente Marketing")

        # Documentos generados
        n = GeneratedDocument.query.filter_by(user_phone=phone).delete()
        print(f"  Documentos generados:         {n}")

        # Incidencias postventa
        n = Incident.query.filter_by(user_phone=phone).delete()
        print(f"  Incidencias eliminadas:       {n}")

        # Metricas LLM
        n = LLMCall.query.filter_by(user_phone=phone).delete()
        print(f"  Registros LLM eliminados:     {n}")

        # Chunks RAG (solo los de documento, no los del wizard para mantener config)
        n = KnowledgeChunk.query.filter_by(
            user_phone=phone, source_type='document'
        ).delete()
        print(f"  Chunks RAG (docs) eliminados: {n}")

        # Resetear notified_phones en subvenciones para que puedan volver a notificar
        grants_reset = 0
        for grant in Grant.query.all():
            phones = list(grant.notified_phones or [])
            if phone in phones:
                phones.remove(phone)
                grant.notified_phones = phones
                grants_reset += 1
        print(f"  Subvenciones reseteadas:      {grants_reset}")

        db.session.commit()
        print("-" * 45)
        print("  Todo limpio. Listo para ensayar.\n")


if __name__ == '__main__':
    phone = sys.argv[1] if len(sys.argv) > 1 else '630339601'
    reset(phone)
