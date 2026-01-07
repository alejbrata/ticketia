class BusinessCoachAgent:
    """
    Agente PROACTIVO de Salud Financiera y Gamificación.
    Monitoriza el rendimiento del negocio y envía mensajes de refuerzo positivo o alertas.
    """

    def analyze_monthly_performance(self, user_id):
        """
        Compara gastos e ingresos (si los hubiera) del mes actual vs mes anterior.

        Args:
            user_id (int): ID del usuario.
            
        Returns:
            dict: Estadísticas clave (% variación, categorías top).
        """
        # TODO: Consultar tabla Ticket y realizar agregaciones
        pass

    def generate_kudos_message(self, stats):
        """
        Crea un mensaje motivacional positivo basado en los datos.
        Evita el tono fiscal aburrido; busca gamificar el ahorro o la gestión.

        Args:
            stats (dict): Estadísticas calculadas.
            
        Returns:
            str: Mensaje 'Kudos' listo para enviar.
        """
        # TODO: Usar templates o LLM para generar mensajes variados y divertidos
        pass
