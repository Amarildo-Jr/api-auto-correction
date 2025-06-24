#!/usr/bin/env python3
"""
Script simplificado para inicializar dados de exemplo
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import User


def main():
    """Inicializar dados de exemplo"""
    print("🚀 Verificando se precisa inicializar dados...")
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se já existem usuários
            if User.query.count() > 0:
                print("ℹ️ Dados já existem no banco. Pulando inicialização.")
                return
            
            print("📊 Executando inicialização completa do banco...")
            
            # Importar e executar init_db_in_context
            from init_db import init_db_in_context
            init_db_in_context()
            
            print("✅ Inicialização completa!")
            
        except Exception as e:
            print(f"❌ Erro durante a inicialização: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main() 