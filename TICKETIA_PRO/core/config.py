import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_super_secret_123'

    # Database Config
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    _instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(_instance_dir, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = uri or 'sqlite:///' + os.path.join(_instance_dir, 'zeptai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session security
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True   # JS no puede leer la cookie de sesion
    SESSION_COOKIE_SAMESITE = 'Lax' # Proteccion CSRF basica
    # En produccion con HTTPS, activar: SESSION_COOKIE_SECURE = True
    
    # NUEVO: URL Pública para webhooks y medios (ngrok o dominio real)
    # Elimina la barra final si el usuario la pone
    PUBLIC_URL = os.environ.get('PUBLIC_URL', 'https://stepless-janel-bashfully.ngrok-free.dev').rstrip('/')

    # Mail Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # RunwayML Config
    RUNWAYML_API_SECRET = os.environ.get('RUNWAYML_API_SECRET')
