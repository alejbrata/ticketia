# Usa una imagen base oficial de Python (Slim es más ligera pero basada en Debian, por lo que pandas y psycopg2 compilan bien)
FROM python:3.11-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE 1
# Evita que Python haga buffer stdout y stderr (útil para ver logs en Docker)
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para compilar paquetes (ej. psycopg2) y otras utilidades
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos primero para aprovechar el caché de capas de Docker
COPY requirements.txt .

# Instala las dependencias de Python
# Añadimos netmiko o librerias pesadas sin cache para aligerar la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido de la aplicación al contenedor
COPY ./TICKETIA_PRO /app/TICKETIA_PRO

# Cambia al directorio de la aplicación
WORKDIR /app/TICKETIA_PRO

# Expone el puerto en el que correrá Flask
EXPOSE 5000

# Comando para ejecutar la aplicación (usamos el servidor por defecto de Flask para desarrollo/demo)
CMD ["python", "app.py"]
