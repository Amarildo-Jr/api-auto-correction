import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Carregar variáveis de ambiente
load_dotenv()

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Determinar o ambiente
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Carregar configurações baseadas no ambiente
    from config import config
    app.config.from_object(config[config_name])
    
    # Configurar CORS
    if hasattr(app.config, 'CORS_ORIGINS'):
        CORS(app, origins=app.config['CORS_ORIGINS'])
    else:
        CORS(app)
    
    # Inicializar extensões
    from database import db, jwt
    db.init_app(app)
    jwt.init_app(app)
    
    # Registrar rotas
    from routes import register_routes
    register_routes(app)
    
    # Handlers de erro personalizados
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Recurso não encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'message': 'Erro interno do servidor'}), 500
    
    # Health check endpoint para o Render
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'environment': config_name,
            'database': 'connected' if db.engine else 'disconnected'
        }), 200
    
    return app

# Para execução local
if __name__ == '__main__':
    app = create_app()
    
    # Criar tabelas se não existirem
    with app.app_context():
        from database import db
        try:
            db.create_all()
            print("✅ Tabelas do banco de dados criadas/verificadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
    
    # Executar aplicação
    port = int(os.getenv('PORT', 5000))
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=port
    ) 