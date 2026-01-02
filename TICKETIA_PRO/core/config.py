import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_super_secret_123'
    
    # Database Config
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri or 'sqlite:///instance/zeptai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
