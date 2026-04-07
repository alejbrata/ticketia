# 🎓 Guía de Ejecución para Defensa TFM

Sigue estos pasos para levantar el entorno completo de Ticketia (Zeptai) durante la demostración en vivo.

## 1. Terminal Principal: La Aplicación Web
Esta terminal levanta el servidor Flask, la interfaz web y los agentes inteligentes (incluido "El Consejo").

```powershell
# Desde la carpeta raíz del proyecto
cd TICKETIA_PRO
python app.py
```

*   **Estado**: Esperar a ver `Running on http://0.0.0.0:5000`.
*   **Acceso**: Abre [http://localhost:5000](http://localhost:5000) en tu navegador.

## 2. Terminal Secundaria: El Scheduler (Opcional)
Esta terminal ejecuta los procesos en segundo plano, como el **Business Coach** que analiza las finanzas diariamente.

```powershell
# Abre una SEGUNDA terminal
cd TICKETIA_PRO
python run_scheduler.py
```

*   **Estado**: Verás un mensaje `🚀 Scheduler Activo`.
*   **Nota**: Si no lo lanzas, la web funciona igual, pero no habrá notificaciones *push* proactivas simuladas en segundo plano.

## 3. Despliegue Rápido con Docker (Para Evaluadores)
Si prefieres no instalar dependencias de Python localmente, puedes levantar todo el ecosistema (Web + Scheduler) con Docker Compose:

```powershell
# Asegúrate de tener Docker Desktop iniciado
docker-compose up --build
```
*   **Estado**: La app estará disponible en [http://localhost:5000](http://localhost:5000).
*   **Detener**: Pulsa `Ctrl+C` o ejecuta `docker-compose down`.

## 4. Credenciales y Datos Demo
Si necesitas loguearte durante la demo:
*   **Teléfono**: El que has configurado en `seed_owner.py` (ej: `+34600...`).
*   **Resetear Datos**: Si quieres empezar de cero antes del tribunal:
    ```powershell
    python reset_db_full.py
    ```
    *(¡Cuidado! Borra todo y crea un usuario limpio).*

## 5. Guion Rápido de Demo (Checklist)
1.  **Login/Dashboard**: Mostrar KPIs y gráfica de gastos.
2.  **Subir Ticket**: Usar el botón de la cámara (simulado) y ver cómo la IA extrae el dato.
3.  **El Consejo (WOW)**: Ir a "Sala de Juntas", lanzar una pregunta estratégica y dejar que debatan.
4.  **Generar Documento**: Pedir al bot que genere un PDF o Excel.
5.  **Demostración MCP (Extra)**: Explicar cómo los agentes ahora son Locales-Primero. Mostrar el servidor `mcp_server_sse.py` u Open una nueva terminal y lanzar `python test_council_async.py` para demostrar cómo el agente busca en internet el BOE en tiempo real.
