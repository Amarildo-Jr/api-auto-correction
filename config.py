import os
from datetime import timedelta


class Config:
    """Configuração base"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Google Generative AI
    GOOGLE_GENAI_API_KEY = os.getenv('GOOGLE_GENAI_API_KEY')

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Banco local - pode usar PostgreSQL local ou Docker
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:postgres@localhost:5432/ufpi_ic'
    )
    
    # CORS mais permissivo para desenvolvimento
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

class ProductionConfig(Config):
    """Configuração para produção (Render)"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # No Render, a DATABASE_URL é fornecida automaticamente quando você conecta um PostgreSQL
    # Render também adiciona automaticamente as configurações de SSL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Para o Render, precisamos configurar o SSL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # CORS específico para produção - coloque aqui o domínio do seu frontend
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    
    # Configurações adicionais de segurança para produção
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 30,
        }
    }

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)

# Dicionário para facilitar a seleção da configuração
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 