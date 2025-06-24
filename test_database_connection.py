#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados
Útil para verificar se a configuração está correta
"""
import os
import sys

from sqlalchemy import create_engine, text


def test_database_connection():
    """Testa a conexão com o banco de dados"""
    
    # Obter DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL não encontrada!")
        print("Configure a variável de ambiente DATABASE_URL")
        return False
    
    print(f"🔗 Testando conexão com: {database_url.split('@')[0]}@[HIDDEN]")
    
    try:
        # Criar engine
        engine = create_engine(database_url)
        
        # Testar conexão
        with engine.connect() as connection:
            # Teste básico
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            print("✅ Conexão com banco estabelecida com sucesso!")
            print(f"📊 Versão do PostgreSQL: {version}")
            
            # Verificar se as tabelas existem
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"📋 Tabelas encontradas ({len(tables)}):")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  Nenhuma tabela encontrada. Execute 'python init_render_db.py' para criar as tabelas.")
            
            # Testar algumas queries básicas se as tabelas existirem
            if 'users' in tables:
                result = connection.execute(text("SELECT COUNT(*) FROM users;"))
                user_count = result.fetchone()[0]
                print(f"👥 Usuários cadastrados: {user_count}")
                
                if user_count > 0:
                    result = connection.execute(text("""
                        SELECT username, email, role 
                        FROM users 
                        LIMIT 3;
                    """))
                    users = result.fetchall()
                    print("👤 Usuários de exemplo:")
                    for user in users:
                        print(f"   - {user[0]} ({user[1]}) - {user[2]}")
            
            if 'subjects' in tables:
                result = connection.execute(text("SELECT COUNT(*) FROM subjects;"))
                subject_count = result.fetchone()[0]
                print(f"📚 Matérias cadastradas: {subject_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verifique se DATABASE_URL está correta")
        print("2. Confirme se o banco PostgreSQL está rodando")
        print("3. Verifique as configurações de rede/firewall")
        return False

def test_environment():
    """Testa as configurações do ambiente"""
    print("🔍 Verificando configurações do ambiente...\n")
    
    # Variáveis importantes
    env_vars = [
        'DATABASE_URL',
        'FLASK_ENV',
        'JWT_SECRET_KEY',
        'GOOGLE_GENAI_API_KEY',
        'CORS_ORIGINS'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mascarar valores sensíveis
            if 'KEY' in var or 'URL' in var:
                display_value = f"{value[:10]}..." if len(value) > 10 else "[HIDDEN]"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚠️  {var}: não definida")
    
    print()

if __name__ == '__main__':
    print("🧪 Teste de Conexão com Banco de Dados")
    print("=" * 50)
    
    # Testar ambiente
    test_environment()
    
    # Testar conexão
    success = test_database_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Todos os testes passaram!")
        print("✅ Banco de dados está configurado e funcionando corretamente.")
    else:
        print("❌ Falha nos testes!")
        print("🔧 Verifique as configurações e tente novamente.")
    
    sys.exit(0 if success else 1) 