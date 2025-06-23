from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print("Token inválido:", error_string)
    return jsonify({'message': 'Token inválido', 'error': error_string}), 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    print("Token não fornecido:", error_string)
    return jsonify({'message': 'Token não fornecido', 'error': error_string}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("Token expirado:", jwt_payload)
    return jsonify({'message': 'Token expirado'}), 401

@jwt.user_identity_loader
def user_identity_lookup(user):
    print("Identidade do usuário:", user)
    return user

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    print("Dados do JWT:", jwt_data)
    identity = jwt_data["sub"]
    from models import User
    return User.query.filter_by(id=identity).one_or_none() 