#!/usr/bin/env python3
"""
Script para forçar a reinicialização do banco com dados de teste
CUIDADO: Este script limpa todos os dados existentes!
"""
import os
import sys

from app import create_app


def force_reinit():
    """Forçar reinicialização completa do banco"""
    
    print("⚠️  ATENÇÃO: Este script irá LIMPAR todos os dados existentes!")
    print("📊 Forçando reinicialização do banco de dados...")
    
    # Verificar se DATABASE_URL existe
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL não encontrada!")
        return False
    
    try:
        # Criar aplicação
        app = create_app('production')
        
        with app.app_context():
            from database import db
            from models import User
            
            print(f"📈 Usuários antes da limpeza: {User.query.count()}")
            
            # Dropar todas as tabelas
            print("🗑️  Removendo todas as tabelas...")
            db.drop_all()
            
            # Recriar todas as tabelas
            print("🏗️  Recriando estrutura do banco...")
            db.create_all()
            
            # Executar inicialização completa
            print("📊 Executando inicialização completa...")
            from init_db import init_db_in_context
            init_db_in_context()
            
            print(f"📈 Usuários após inicialização: {User.query.count()}")
            
            # Verificar usuários de teste
            prof_test = User.query.filter_by(email='prof1@exemplo.com').first()
            student_test = User.query.filter_by(email='aluno1@exemplo.com').first()
            admin_test = User.query.filter_by(role='admin').first()
            
            print("\n🧪 Verificação dos usuários criados:")
            print(f"   👑 Admin: {'✅' if admin_test else '❌'} ({admin_test.email if admin_test else 'N/A'})")
            print(f"   👨‍🏫 Professor: {'✅' if prof_test else '❌'} (prof1@exemplo.com)")
            print(f"   👨‍🎓 Aluno: {'✅' if student_test else '❌'} (aluno1@exemplo.com)")
            
            print("\n🎉 Banco reinicializado com sucesso!")
            print("🔐 Credenciais de teste:")
            print("   Professor: prof1@exemplo.com / 123456")
            print("   Aluno: aluno1@exemplo.com / 123456")
            if admin_test:
                print(f"   Admin: {admin_test.email} / admin123")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro durante reinicialização: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = force_reinit()
    sys.exit(0 if success else 1) 