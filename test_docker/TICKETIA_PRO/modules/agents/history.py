from core.db_models import db, ChatMessage

class HistoryService:
    @staticmethod
    def get_recent_history(phone, limit=10):
        """
        Recupera el historial reciente de chat para un usuario específico.
        Devuelve formato compatible con OpenAI API.
        """
        # Obtenemos los últimos 'limit' mensajes (orden descendente por fecha)
        messages_db = ChatMessage.query.filter_by(user_phone=phone)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(limit)\
            .all()
            
        # Revertimos para tener orden cronológico (antiguo -> nuevo)
        messages_db.reverse()
        
        history = []
        for msg in messages_db:
            msg_dict = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
                # Si es tool response, necesita el campo 'name' (que no guardamos, pero el role es 'tool')
                # En implementación estricta, deberíamos guardar 'name' también en DB.
                # Para simplificar, si es 'tool', asumimos que el manager lo maneja o que no es crítico para re-hidratar contexto simple.
                # Nota: OpenAI requiere 'tool_call_id' para role='tool'.
                pass
                
            history.append(msg_dict)
            
        return history

    @staticmethod
    def save_interaction(phone, role, content, tool_call_id=None):
        """
        Guarda un mensaje en el historial.
        """
        try:
            new_msg = ChatMessage(
                user_phone=phone,
                role=role,
                content=content,
                tool_call_id=tool_call_id
            )
            db.session.add(new_msg)
            
            # --- AUTO-CLEANUP (Log Rotation) ---
            # 1. Contar mensajes actuales del usuario (incluyendo el nuevo pendiente de commit)
            # count() de query es eficiente
            current_count = ChatMessage.query.filter_by(user_phone=phone).count()
            
            MAX_HISTORY = 50
            KEEP_COUNT = 40
            
            if current_count > MAX_HISTORY:
                # 2. Identificar mensajes viejos a borrar
                # Queremos dejar solo los KEEP_COUNT más recientes.
                # Borramos los (current_count - KEEP_COUNT) más antiguos.
                to_delete_count = current_count - KEEP_COUNT
                
                # Subconsulta para obtener IDs de los más viejos
                # Ordenamos por fecha ASC (viejos primero) y limitamos a to_delete_count
                old_messages = ChatMessage.query.filter_by(user_phone=phone)\
                    .order_by(ChatMessage.created_at.asc())\
                    .limit(to_delete_count)\
                    .all()
                
                for old_msg in old_messages:
                    db.session.delete(old_msg)
                    
                print(f"🧹 History Cleanup: Deleted {len(old_messages)} old messages for {phone}")

            db.session.commit()
        except Exception as e:
            print(f"Error saving history: {e}")
