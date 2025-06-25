#!/usr/bin/env python3
"""
Script para criar usuários de teste no banco de produção (Render)
Execute este script após o deploy inicial
"""
import os
import sys

from app import create_app


def create_test_users():
    """Criar usuários de teste"""
    
    # Verificar se DATABASE_URL existe
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL não encontrada!")
        return False
    
    try:
        # Criar aplicação
        print("🚀 Conectando ao banco de dados...")
        app = create_app('production')
        
        with app.app_context():
            from database import db
            from models import User
            from werkzeug.security import generate_password_hash

            # Verificar se os usuários de teste já existem
            existing_prof = User.query.filter_by(email='prof1@exemplo.com').first()
            existing_student = User.query.filter_by(email='aluno1@exemplo.com').first()
            
            if existing_prof and existing_student:
                print("✅ Usuários de teste já existem!")
                return True
            
            # Criar professor de teste
            if not existing_prof:
                print("👨‍🏫 Criando professor de teste...")
                professor = User(
                    username='prof1',
                    email='prof1@exemplo.com',
                    password_hash=generate_password_hash('123456'),
                    name='Dr. João Silva',
                    role='professor',
                    is_active=True
                )
                db.session.add(professor)
                print("✅ Professor criado: prof1@exemplo.com / 123456")
            
            # Criar aluno de teste
            if not existing_student:
                print("👨‍🎓 Criando aluno de teste...")
                student = User(
                    username='aluno1',
                    email='aluno1@exemplo.com',
                    password_hash=generate_password_hash('123456'),
                    name='Pedro Oliveira',
                    role='student',
                    is_active=True
                )
                db.session.add(student)
                print("✅ Aluno criado: aluno1@exemplo.com / 123456")
            
            # Salvar no banco
            db.session.commit()
            
            print("🎉 Usuários de teste criados com sucesso!")
            print("\n📝 Credenciais para teste:")
            print("   Professor: prof1@exemplo.com / 123456")
            print("   Aluno: aluno1@exemplo.com / 123456")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar usuários de teste: {e}")
        return False

if __name__ == '__main__':
    success = create_test_users()
    sys.exit(0 if success else 1) 