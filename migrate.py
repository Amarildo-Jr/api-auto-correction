#!/usr/bin/env python3
"""
Script para executar migrações do banco de dados
"""

import os
import sys

from app import create_app
from database import db
from init_db import apply_migrations


def main():
    """Executar migrações"""
    print("🚀 Iniciando processo de migração...")
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        try:
            # Aplicar migrações
            apply_migrations()
            
            # Commit das mudanças
            db.session.commit()
            print("✅ Migrações aplicadas com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    main() 