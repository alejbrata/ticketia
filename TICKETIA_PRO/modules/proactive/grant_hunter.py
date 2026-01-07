class GrantHunterAgent:
    """
    Agente PROACTIVO encargado de monitorizar oportunidades de financiación y ayudas.
    Actúa como un 'Buscador de Subvenciones' automático para cada perfil de negocio.
    """

    def check_new_grants(self, user_profile):
        """
        Simula la conexión con fuentes de datos externas (BOE, Bases de Datos de Subvenciones).
        Filtra las ayudas basándose en el sector y ubicación del usuario.

        Args:
            user_profile (BusinessProfile): El perfil del negocio a analizar.
        
        Returns:
            list: Lista de diccionarios con detalles de las ayudas encontradas.
        """
        # TODO: Implementar scraping o conexión API a fuente de ayudas
        pass

    def notify_opportunity(self, user_phone, grant_details):
        """
        Envía una alerta proactiva al usuario sobre una oportunidad detectada.

        Args:
            user_phone (str): Teléfono del usuario.
            grant_details (dict): Detalles de la ayuda (Título, Plazo, Importe).
        """
        # TODO: Integrar con servicio de mensajería (WhatsApp/Email)
        pass
