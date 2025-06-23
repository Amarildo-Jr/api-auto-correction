import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configurações
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/exam_db')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações adicionais do JWT
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens não expiram
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'

    # Inicializar extensões
    from database import db, jwt
    db.init_app(app)
    jwt.init_app(app)

    # Registrar rotas
    from routes import register_routes
    register_routes(app)

    # Handler de erro para JWT
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        print("Token inválido:", error_string)
        return jsonify({'message': 'Token inválido', 'error': error_string}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        print("Token não fornecido:", error_string)
        return jsonify({'message': 'Token não fornecido', 'error': error_string}), 401

    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        from database import db
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 