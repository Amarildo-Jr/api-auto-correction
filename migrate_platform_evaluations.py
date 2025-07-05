#!/usr/bin/env python3
"""
Script de migração para adicionar a tabela platform_evaluations
Execute este script para criar a nova tabela no banco de dados em produção
"""

import os
import sys
from datetime import datetime

# Config será importado dinamicamente baseado no ambiente
from database import db
from flask import Flask


def create_app():
    """Criar aplicação Flask para migração"""
    app = Flask(__name__)
    
    # Determinar configuração baseada no ambiente
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        from config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Verificar se DATABASE_URL foi configurada
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        # Tentar variáveis de ambiente diretamente
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            raise ValueError("DATABASE_URL não configurada!")
    
    print(f"📊 Configuração de banco: {database_url[:50]}...")
    
    # Inicializar banco de dados
    db.init_app(app)
    
    return app

def create_platform_evaluations_table():
    """Criar a tabela platform_evaluations"""
    
    # SQL para criar a tabela
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS platform_evaluations (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        
        -- Avaliações gerais (escala 1-5)
        design_rating INTEGER NOT NULL,
        colors_rating INTEGER NOT NULL,
        layout_rating INTEGER NOT NULL,
        responsiveness_rating INTEGER NOT NULL,
        
        -- Navegação e Usabilidade
        navigation_rating INTEGER NOT NULL,
        menus_rating INTEGER NOT NULL,
        loading_speed_rating INTEGER NOT NULL,
        instructions_rating INTEGER NOT NULL,
        
        -- Funcionalidades
        registration_rating INTEGER NOT NULL,
        login_rating INTEGER NOT NULL,
        class_enrollment_rating INTEGER NOT NULL,
        exam_taking_rating INTEGER NOT NULL,
        results_rating INTEGER NOT NULL,
        
        -- Experiência específica
        registration_ease VARCHAR(20) NOT NULL,
        registration_problems TEXT,
        login_intuitive BOOLEAN NOT NULL,
        login_comments TEXT,
        
        -- Navegação na turma
        class_finding_easy BOOLEAN NOT NULL,
        class_finding_comments TEXT,
        class_process_clear BOOLEAN NOT NULL,
        class_process_comments TEXT,
        
        -- Realização da prova
        exam_instructions_clear BOOLEAN NOT NULL,
        exam_instructions_comments TEXT,
        timer_visible BOOLEAN NOT NULL,
        timer_comments TEXT,
        question_navigation_easy BOOLEAN NOT NULL,
        question_navigation_comments TEXT,
        answer_area_adequate BOOLEAN NOT NULL,
        answer_area_comments TEXT,
        exam_finish_difficulty BOOLEAN NOT NULL,
        exam_finish_comments TEXT,
        
        -- Resultados
        results_clear BOOLEAN NOT NULL,
        results_comments TEXT,
        essay_feedback_useful BOOLEAN,
        essay_feedback_comments TEXT,
        
        -- Problemas encontrados
        technical_errors BOOLEAN NOT NULL,
        technical_errors_description TEXT,
        functionality_issues BOOLEAN NOT NULL,
        functionality_issues_description TEXT,
        
        -- Dificuldades de uso
        confusion_moments BOOLEAN NOT NULL,
        confusion_description TEXT,
        missing_features BOOLEAN NOT NULL,
        missing_features_description TEXT,
        
        -- Sugestões
        platform_changes TEXT,
        desired_features TEXT,
        ux_suggestions TEXT,
        
        -- Avaliação final
        recommendation VARCHAR(30) NOT NULL,
        general_impression VARCHAR(20) NOT NULL,
        additional_comments TEXT,
        
        -- Informações técnicas
        device_type VARCHAR(20) NOT NULL,
        browser VARCHAR(50) NOT NULL,
        operating_system VARCHAR(50) NOT NULL,
        
        -- Metadados
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Constraint para garantir uma avaliação por usuário
        UNIQUE(user_id)
    );
    """
    
    # Índices para melhor performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_platform_evaluations_user_id ON platform_evaluations(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_platform_evaluations_created_at ON platform_evaluations(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_platform_evaluations_recommendation ON platform_evaluations(recommendation);",
        "CREATE INDEX IF NOT EXISTS idx_platform_evaluations_general_impression ON platform_evaluations(general_impression);"
    ]
    
    try:
        # Executar criação da tabela
        print("🔄 Criando tabela platform_evaluations...")
        db.session.execute(db.text(create_table_sql))
        print("✅ Tabela platform_evaluations criada com sucesso!")
        
        # Executar criação dos índices
        print("🔄 Criando índices...")
        for index_sql in create_indexes_sql:
            db.session.execute(db.text(index_sql))
        print("✅ Índices criados com sucesso!")
        
        # Commit das mudanças
        db.session.commit()
        print("✅ Migração concluída com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {str(e)}")
        db.session.rollback()
        return False

def verify_table_creation():
    """Verificar se a tabela foi criada corretamente"""
    try:
        # Verificar se a tabela existe
        result = db.session.execute(db.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'platform_evaluations'
            );
        """))
        
        table_exists = result.scalar()
        
        if table_exists:
            print("✅ Verificação: Tabela platform_evaluations existe")
            
            # Verificar estrutura da tabela
            result = db.session.execute(db.text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'platform_evaluations'
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            print(f"✅ Verificação: Tabela possui {len(columns)} colunas")
            
            # Verificar constraint UNIQUE
            result = db.session.execute(db.text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'platform_evaluations' 
                AND constraint_type = 'UNIQUE';
            """))
            
            constraints = result.fetchall()
            if constraints:
                print("✅ Verificação: Constraint UNIQUE(user_id) aplicada")
            else:
                print("⚠️  Aviso: Constraint UNIQUE(user_id) não encontrada")
            
            return True
        else:
            print("❌ Verificação: Tabela platform_evaluations não foi criada")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação: {str(e)}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 MIGRAÇÃO: Criação da tabela platform_evaluations")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('models.py'):
        print("❌ Erro: Execute este script no diretório api-auto-correction")
        sys.exit(1)
    
    # Criar aplicação e contexto
    app = create_app()
    
    with app.app_context():
        try:
            # Testar conexão com o banco
            print("🔄 Testando conexão com o banco de dados...")
            db.session.execute(db.text("SELECT 1"))
            print("✅ Conexão com banco estabelecida")
            print()
            
            # Verificar se a tabela já existe
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'platform_evaluations'
                );
            """))
            
            if result.scalar():
                print("⚠️  A tabela platform_evaluations já existe!")
                print("   Pulando criação da tabela...")
                print()
            else:
                # Criar tabela
                if not create_platform_evaluations_table():
                    print("❌ Falha na migração!")
                    sys.exit(1)
                print()
            
            # Verificar criação
            if verify_table_creation():
                print()
                print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                print("   A tabela platform_evaluations está pronta para uso.")
                print("   As rotas da API podem agora ser utilizadas.")
            else:
                print("❌ FALHA NA VERIFICAÇÃO!")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Erro fatal: {str(e)}")
            sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main() 