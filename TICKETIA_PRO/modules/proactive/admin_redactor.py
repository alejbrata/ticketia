class AdminAssistantAgent:
    """
    Agente PROACTIVO (o Reactivo avanzado) para tareas burocráticas.
    Transforma inputs informales (fotos, notas de voz) en documentos formales.
    """

    def draft_document_from_image(self, image_url, doc_type):
        """
        Transforma foto de borrador/servilleta -> Texto formal (PDF/Email).

        Args:
            image_url (str): URL de la imagen input.
            doc_type (str): Tipo de documento deseado (ej: 'presupuesto', 'carta_formal').
            
        Returns:
            str: Texto redactado formalmente.
        """
        # TODO: Integrar con OpenAI Vision API para leer la imagen y generar texto
        pass

    def send_draft_to_user(self, draft_text):
        """
        Solicita validación al usuario antes del envío final o generación de PDF.

        Args:
            draft_text (str): El borrador generado.
        """
        # TODO: Enviar mensaje interactivo ('¿Te parece bien este borrador?')
        pass
