from core.db_models import db, ChatMessage

MAX_HISTORY = 50   # trigger cleanup above this
KEEP_COUNT   = 40  # messages to keep after cleanup

class HistoryService:
    @staticmethod
    def get_recent_history(phone, limit=10):
        """
        Recupera el historial reciente de chat en orden cronológico.
        Devuelve formato compatible con OpenAI API (incluyendo campo 'name'
        para mensajes role='tool', obligatorio en strict mode).
        """
        messages_db = (
            ChatMessage.query
            .filter_by(user_phone=phone)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        messages_db.reverse()  # cronológico: antiguo → nuevo

        history = []
        for msg in messages_db:
            msg_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                msg_dict["name"] = msg.name
            history.append(msg_dict)

        return history

    @staticmethod
    def save_interaction(phone, role, content, tool_call_id=None, name=None):
        """
        Guarda un mensaje en el historial con limpieza automática.
        'name' es obligatorio para role='tool' (nombre de la función llamada).
        """
        try:
            new_msg = ChatMessage(
                user_phone=phone,
                role=role,
                content=content,
                tool_call_id=tool_call_id,
                name=name
            )
            db.session.add(new_msg)

            # Auto-cleanup: contamos ANTES del commit del nuevo mensaje
            # +1 porque el nuevo ya está en la sesión pero no en el count de DB
            current_count = ChatMessage.query.filter_by(user_phone=phone).count() + 1

            if current_count > MAX_HISTORY:
                to_delete_count = current_count - KEEP_COUNT
                old_messages = (
                    ChatMessage.query
                    .filter_by(user_phone=phone)
                    .order_by(ChatMessage.created_at.asc())
                    .limit(to_delete_count)
                    .all()
                )
                for old_msg in old_messages:
                    db.session.delete(old_msg)
                print(f"History cleanup: deleted {len(old_messages)} old messages for {phone}")

            db.session.commit()
        except Exception as e:
            print(f"Error saving history: {e}")
            db.session.rollback()
