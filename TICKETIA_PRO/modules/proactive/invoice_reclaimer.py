class ReclaimerAgent:
    """
    Agente PROACTIVO 'Reclamador de Facturas'.
    Audita los tickets recibidos para asegurar que cumplen la normativa fiscal.
    """

    def detect_invoice_errors(self, ticket_data):
        """
        Valida si faltan datos críticos (NIF, dirección, desglose IVA) en una factura recibida.

        Args:
            ticket_data (Ticket): Objeto o diccionario con datos del ticket extraídos.
            
        Returns:
            list: Lista de errores detectados (ej: ['Falta NIF cliente', 'Fecha inválida']).
        """
        # TODO: Reglas de validación fiscal (Regex, lógica de negocio)
        pass

    def draft_rectification_email(self, provider_email, error_details):
        """
        Redacta el correo formal solicitando la corrección al proveedor.

        Args:
            provider_email (str): Email del proveedor (si se conoce).
            error_details (list): Errores que motivan la reclamación.
            
        Returns:
            str: Cuerpo del email de reclamación.
        """
        # TODO: Plantilla formal de solicitud de rectificación de factura
        pass
