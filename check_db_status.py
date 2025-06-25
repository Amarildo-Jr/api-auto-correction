#!/usr/bin/env python3
"""
Script para verificar o status do banco de dados no Render
"""
import os
import sys

from app import create_app


def check_database_status():
    """Verificar status do banco de dados"""
    
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL não encontrada!")
        return False
    
    try:
        app = create_app('production')
        
        with app.app_context():
            from database import db
            from models import Class, Exam, Question, User
            
            print("🔍 Verificando status do banco de dados...")
            print(f"📊 DATABASE_URL: {os.getenv('DATABASE_URL')[:50]}...")
            
            # Verificar conexão
            try:
                db.session.execute('SELECT 1')
                print("✅ Conexão com banco OK")
            except Exception as e:
                print(f"❌ Erro de conexão: {e}")
                return False
            
            # Contar registros
            users_count = User.query.count()
            classes_count = Class.query.count()
            exams_count = Exam.query.count()
            questions_count = Question.query.count()
            
            print(f"\n📈 Estatísticas do banco:")
            print(f"   👥 Usuários: {users_count}")
            print(f"   📚 Turmas: {classes_count}")
            print(f"   📝 Exames: {exams_count}")
            print(f"   ❓ Questões: {questions_count}")
            
            # Verificar usuários por role
            admins = User.query.filter_by(role='admin').count()
            professors = User.query.filter_by(role='professor').count()
            students = User.query.filter_by(role='student').count()
            
            print(f"\n👤 Usuários por tipo:")
            print(f"   👑 Admins: {admins}")
            print(f"   👨‍🏫 Professores: {professors}")
            print(f"   👨‍🎓 Alunos: {students}")
            
            # Verificar usuários de teste específicos
            prof_test = User.query.filter_by(email='prof1@exemplo.com').first()
            student_test = User.query.filter_by(email='aluno1@exemplo.com').first()
            
            print(f"\n🧪 Usuários de teste:")
            print(f"   prof1@exemplo.com: {'✅ Existe' if prof_test else '❌ Não existe'}")
            print(f"   aluno1@exemplo.com: {'✅ Existe' if student_test else '❌ Não existe'}")
            
            if prof_test:
                print(f"      - Nome: {prof_test.name}")
                print(f"      - Role: {prof_test.role}")
                print(f"      - Ativo: {prof_test.is_active}")
            
            if student_test:
                print(f"      - Nome: {student_test.name}")
                print(f"      - Role: {student_test.role}")
                print(f"      - Ativo: {student_test.is_active}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

if __name__ == '__main__':
    success = check_database_status()
    sys.exit(0 if success else 1) 