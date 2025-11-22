import os
from datetime import timedelta

class Config:
    # Configuración básica de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-super-segura-aqui'
    
    # Configuración de base de datos
    # En producción, usar volumen montado si existe, sino usar directorio actual
    if os.path.exists('/app/data'):
        DATABASE_PATH = '/app/data/diagnostico.db'
    else:
        DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagnostico.db')
    
    # Configuración de Gemini AI
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'TU_API_KEY_DE_GEMINI_AQUI'
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Configuración de PDF
    PDF_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdfs')
    
    # Configuración de correo (para futuras implementaciones)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configuración de la aplicación
    APP_NAME = 'Ruta de Estrategia Digital'
    APP_VERSION = '1.0.0'
    APP_DESCRIPTION = 'Herramienta de estrategia digital para emprendimientos en gestación'
    
    @staticmethod
    def init_app(app):
        # Crear directorios necesarios
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PDF_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ':memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}