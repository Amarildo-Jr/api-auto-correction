#!/usr/bin/env python3
"""
Script para atualizar o status das provas expiradas no banco de dados
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import db, init_db
from flask import Flask
from models import Exam


def create_app():
    """Criar aplicação Flask para o script"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar banco de dados
    init_db(app)
    
    return app

def update_expired_exams():
    """Atualizar status das provas que passaram do prazo"""
    try:
        now = datetime.utcnow()
        
        # Buscar provas publicadas que já passaram do prazo
        expired_exams = Exam.query.filter(
            Exam.status == 'published',
            Exam.end_time < now
        ).all()
        
        if not expired_exams:
            print("✅ Nenhuma prova expirada encontrada.")
            return 0
        
        print(f"📋 Encontradas {len(expired_exams)} provas expiradas:")
        
        updated_count = 0
        for exam in expired_exams:
            print(f"   - ID {exam.id}: {exam.title} (expirou em {exam.end_time})")
            exam.status = 'finished'
            updated_count += 1
        
        db.session.commit()
        print(f"✅ Atualizadas {updated_count} provas para status 'finished'")
        
        return updated_count
    except Exception as e:
        print(f"❌ Erro ao atualizar provas expiradas: {e}")
        db.session.rollback()
        return 0

def main():
    """Função principal"""
    print("🔧 Iniciando atualização de provas expiradas...")
    
    app = create_app()
    
    with app.app_context():
        update_expired_exams()
    
    print("🎉 Processo concluído!")

if __name__ == '__main__':
    main() 