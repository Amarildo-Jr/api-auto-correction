#!/usr/bin/env python3
"""
Script para inicializar o banco de dados no Render
Execute este script APENAS UMA VEZ após o primeiro deploy
"""
import os
import sys

from app import create_app


def init_database():
    """Inicializa o banco de dados com dados básicos"""
    
    # Verificar se estamos em produção
    if os.getenv('FLASK_ENV') != 'production':
        print("⚠️  Este script deve ser executado apenas em produção!")
        print("Para desenvolvimento, use: python init_db.py")
        return False
    
    # Verificar se DATABASE_URL existe
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL não encontrada!")
        print("Certifique-se de que o PostgreSQL foi conectado no Render.")
        return False
    
    try:
        # Criar aplicação
        print("🚀 Inicializando aplicação...")
        app = create_app('production')
        
        with app.app_context():
            from database import db
            from models import Answer, Class, Exam, Question, Subject, User

            # Criar todas as tabelas
            print("📋 Criando tabelas do banco de dados...")
            db.create_all()
            
            # Verificar se já existe um admin
            admin_exists = User.query.filter_by(role='admin').first()
            
            if not admin_exists:
                print("👤 Criando usuário administrador padrão...")
                
                # Criar admin padrão
                from werkzeug.security import generate_password_hash
                
                admin_user = User(
                    username='admin',
                    email='admin@ufpi.edu.br',
                    password_hash=generate_password_hash('admin123'),  # MUDE ESTA SENHA!
                    role='admin',
                    is_active=True
                )
                
                db.session.add(admin_user)
                db.session.commit()
                
                print("✅ Usuário administrador criado!")
                print("📧 Email: admin@ufpi.edu.br")
                print("🔐 Senha: admin123")
                print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
            else:
                print("✅ Usuário administrador já existe.")
            
            # Criar algumas matérias de exemplo se não existirem
            if Subject.query.count() == 0:
                print("📚 Criando matérias de exemplo...")
                
                subjects = [
                    Subject(name='Matemática', description='Disciplina de Matemática'),
                    Subject(name='Português', description='Disciplina de Língua Portuguesa'),
                    Subject(name='História', description='Disciplina de História'),
                    Subject(name='Geografia', description='Disciplina de Geografia'),
                ]
                
                for subject in subjects:
                    db.session.add(subject)
                
                db.session.commit()
                print("✅ Matérias de exemplo criadas!")
            
            print("🎉 Banco de dados inicializado com sucesso!")
            print("🔗 Acesse sua aplicação e faça login como administrador.")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1) 