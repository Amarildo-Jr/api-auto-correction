import os
import random
from datetime import datetime, timedelta

from app import create_app
from dotenv import load_dotenv

load_dotenv()
from database import db
from models import Alternative, Class, ClassEnrollment, Exam, Question, User
from werkzeug.security import generate_password_hash


def check_column_exists(table_name, column_name):
    """Verificar se uma coluna existe na tabela"""
    try:
        from sqlalchemy import text
        result = db.session.execute(text(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """))
        return result.fetchone() is not None
    except Exception:
        return False


def apply_migrations():
    """Aplicar migrações v3 - Sistema de questões avançado"""
    try:
        from sqlalchemy import text
        
        print("🔄 Aplicando migrações v3...")
        
        # 1. Adicionar campo is_public às questões
        if not check_column_exists('questions', 'is_public'):
            try:
                db.session.execute(text("ALTER TABLE questions ADD COLUMN is_public BOOLEAN DEFAULT TRUE"))
                print("✓ Campo 'is_public' adicionado às questões")
            except Exception as e:
                print(f"⚠️ Erro ao adicionar is_public: {e}")
        else:
            print("✓ Campo 'is_public' já existe")
        
        # 2. Adicionar colunas necessárias na tabela questions
        columns_to_add = [
            ("created_by", "INTEGER REFERENCES users(id)"),
            ("category", "VARCHAR(100)"),
            ("difficulty", "VARCHAR(20) DEFAULT 'medium'"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_type in columns_to_add:
            if not check_column_exists('questions', column_name):
                try:
                    db.session.execute(text(f"ALTER TABLE questions ADD COLUMN {column_name} {column_type}"))
                    print(f"✓ Coluna '{column_name}' adicionada à tabela questions")
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar {column_name}: {e}")
            else:
                print(f"✓ Coluna '{column_name}' já existe")
        
        # 3. Criar tabela exam_questions para pontuação específica
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS exam_questions (
                    id SERIAL PRIMARY KEY,
                    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    points DECIMAL(5,2) NOT NULL,
                    order_number INTEGER NOT NULL,
                    question_snapshot JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(exam_id, question_id)
                )
            """))
            print("✓ Tabela 'exam_questions' criada/verificada")
        except Exception as e:
            print(f"⚠️ Erro ao criar exam_questions: {e}")
        
        # 4. Criar índices para exam_questions
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_exam_questions_exam_id ON exam_questions(exam_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_questions_question_id ON exam_questions(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_questions_order ON exam_questions(exam_id, order_number)"
        ]
        
        for index_sql in indices:
            try:
                db.session.execute(text(index_sql))
            except Exception as e:
                print(f"⚠️ Erro ao criar índice: {e}")
        print("✓ Índices criados/verificados para exam_questions")
        
        # 5. Atualizar tabela answers para selected_alternatives
        if not check_column_exists('answers', 'selected_alternatives'):
            try:
                db.session.execute(text("ALTER TABLE answers ADD COLUMN selected_alternatives JSONB"))
                print("✓ Campo 'selected_alternatives' adicionado")
            except Exception as e:
                print(f"⚠️ Erro ao adicionar selected_alternatives: {e}")
        else:
            print("✓ Campo 'selected_alternatives' já existe")
        
        # 6. Migrar dados existentes de selected_alternative_id para selected_alternatives
        if check_column_exists('answers', 'selected_alternative_id'):
            try:
                db.session.execute(text("""
                    UPDATE answers 
                    SET selected_alternatives = jsonb_build_array(selected_alternative_id)
                    WHERE selected_alternative_id IS NOT NULL AND selected_alternatives IS NULL
                """))
                print("✓ Dados migrados para selected_alternatives")
            except Exception as e:
                print(f"⚠️ Erro na migração de dados: {e}")
        
        # 7. Adicionar campo status na tabela class_enrollments
        if not check_column_exists('class_enrollments', 'status'):
            try:
                db.session.execute(text("ALTER TABLE class_enrollments ADD COLUMN status VARCHAR(50) DEFAULT 'approved'"))
                print("✓ Campo 'status' adicionado às matrículas")
            except Exception as e:
                print(f"⚠️ Erro ao adicionar status: {e}")
        else:
            print("✓ Campo 'status' já existe")
        
        # 8. Alterar colunas para permitir NULL
        try:
            db.session.execute(text("ALTER TABLE questions ALTER COLUMN exam_id DROP NOT NULL"))
            print("✓ Campo 'exam_id' alterado para permitir NULL")
        except Exception as e:
            print(f"⚠️ Erro ao alterar exam_id: {e}")
        
        try:
            db.session.execute(text("ALTER TABLE questions ALTER COLUMN order_number DROP NOT NULL"))
            print("✓ Campo 'order_number' alterado para permitir NULL")
        except Exception as e:
            print(f"⚠️ Erro ao alterar order_number: {e}")
        
        # 9. Criar função para recalcular notas
        try:
            db.session.execute(text("""
                CREATE OR REPLACE FUNCTION recalculate_exam_scores(exam_id_param INTEGER)
                RETURNS TABLE(student_id INTEGER, old_score DECIMAL, new_score DECIMAL) AS $$
                BEGIN
                    RETURN QUERY
                    WITH current_scores AS (
                        SELECT 
                            ee.student_id,
                            COALESCE(SUM(a.points_earned), 0) as current_total
                        FROM exam_enrollments ee
                        LEFT JOIN answers a ON a.enrollment_id = ee.id
                        WHERE ee.exam_id = exam_id_param
                        GROUP BY ee.student_id
                    ),
                    recalculated_scores AS (
                        SELECT 
                            ee.student_id,
                            COALESCE(SUM(
                                CASE 
                                    WHEN q.question_type = 'single_choice' THEN
                                        CASE WHEN a.selected_alternatives::jsonb ? (
                                            SELECT alt.id::text 
                                            FROM alternatives alt 
                                            WHERE alt.question_id = q.id AND alt.is_correct = true
                                            LIMIT 1
                                        ) THEN eq.points ELSE 0 END
                                    WHEN q.question_type = 'multiple_choice' THEN
                                        eq.points * (
                                            SELECT 
                                                CASE 
                                                    WHEN COUNT(*) FILTER (WHERE alt.is_correct AND a.selected_alternatives::jsonb ? alt.id::text) = 
                                                         COUNT(*) FILTER (WHERE alt.is_correct) AND
                                                         COUNT(*) FILTER (WHERE NOT alt.is_correct AND a.selected_alternatives::jsonb ? alt.id::text) = 0
                                                    THEN 1.0
                                                    ELSE 0.0
                                                END
                                            FROM alternatives alt 
                                            WHERE alt.question_id = q.id
                                        )
                                    WHEN q.question_type = 'true_false' THEN
                                        CASE WHEN a.selected_alternatives::jsonb ? (
                                            SELECT alt.id::text 
                                            FROM alternatives alt 
                                            WHERE alt.question_id = q.id AND alt.is_correct = true
                                            LIMIT 1
                                        ) THEN eq.points ELSE 0 END
                                    ELSE 0
                                END
                            ), 0) as new_total
                        FROM exam_enrollments ee
                        LEFT JOIN answers a ON a.enrollment_id = ee.id
                        LEFT JOIN exam_questions eq ON eq.exam_id = ee.exam_id AND eq.question_id = a.question_id
                        LEFT JOIN questions q ON q.id = a.question_id
                        WHERE ee.exam_id = exam_id_param
                        GROUP BY ee.student_id
                    )
                    SELECT 
                        cs.student_id,
                        cs.current_total as old_score,
                        rs.new_total as new_score
                    FROM current_scores cs
                    JOIN recalculated_scores rs ON cs.student_id = rs.student_id
                    WHERE cs.current_total != rs.new_total;
                END;
                $$ LANGUAGE plpgsql;
            """))
            print("✓ Função de recálculo de notas criada")
        except Exception as e:
            print(f"⚠️ Erro ao criar função de recálculo: {e}")
        
        # 10. Adicionar campos de resultado final na tabela exam_enrollments
        result_columns = [
            ("total_points", "DECIMAL(5,2)"),
            ("max_points", "DECIMAL(5,2)"),
            ("percentage", "DECIMAL(5,2)")
        ]
        
        for column_name, column_type in result_columns:
            if not check_column_exists('exam_enrollments', column_name):
                try:
                    db.session.execute(text(f"ALTER TABLE exam_enrollments ADD COLUMN {column_name} {column_type}"))
                    print(f"✓ Coluna '{column_name}' adicionada à tabela exam_enrollments")
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar {column_name}: {e}")
            else:
                print(f"✓ Coluna '{column_name}' já existe na tabela exam_enrollments")
        
        # 11. Atualizar registros existentes
        try:
            db.session.execute(text("UPDATE class_enrollments SET status = 'approved' WHERE status IS NULL OR status = ''"))
            db.session.execute(text("UPDATE questions SET is_public = TRUE WHERE is_public IS NULL"))
            print("✓ Registros existentes atualizados")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar registros: {e}")
        
        db.session.commit()
        print("🎉 Migrações v3 aplicadas com sucesso!")
        
    except Exception as e:
        print(f"⚠️ Erro geral nas migrações: {e}")
        db.session.rollback()


def create_basic_data():
    """Criar dados básicos (usuários, turmas)"""
    print("\n📊 Criando dados básicos...")
    
    # ============================================
    # CRIAÇÃO DE USUÁRIOS
    # ============================================
    
    # Usuário Admin
    admin = User.query.filter_by(email='admin@admin.com').first()
    if not admin:
        admin = User(
            email='admin@admin.com',
            password_hash=generate_password_hash('admin123'),
            name='Administrador',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('✓ Usuário admin criado')
    
    # Professores
    professors = []
    prof_data = [
        ('prof1@ufpi.edu.br', 'Dr. João Silva', 'Matemática'),
        ('prof2@ufpi.edu.br', 'Dra. Maria Santos', 'História'),
        ('prof3@ufpi.edu.br', 'Dr. Carlos Oliveira', 'Ciências'),
        ('prof4@ufpi.edu.br', 'Dra. Ana Costa', 'Programação')
    ]
    
    for email, name, subject in prof_data:
        prof = User.query.filter_by(email=email).first()
        if not prof:
            prof = User(
                email=email,
                password_hash=generate_password_hash('123456'),
                name=name,
                role='professor'
            )
            db.session.add(prof)
            professors.append(prof)
    
    db.session.commit()
    professors = User.query.filter(User.role == 'professor').all()
    print(f'✓ {len(professors)} professores criados/verificados')
    
    # Estudantes
    student_data = [
        ('aluno1@ufpi.edu.br', 'Pedro Oliveira'),
        ('aluno2@ufpi.edu.br', 'Ana Beatriz'),
        ('aluno3@ufpi.edu.br', 'Carlos Lima'),
        ('aluno4@ufpi.edu.br', 'Lucia Fernandes'),
        ('aluno5@ufpi.edu.br', 'Rafael Santos'),
        ('aluno6@ufpi.edu.br', 'Camila Silva'),
        ('aluno7@ufpi.edu.br', 'Bruno Costa'),
        ('aluno8@ufpi.edu.br', 'Juliana Souza')
    ]
    
    for email, name in student_data:
        student = User.query.filter_by(email=email).first()
        if not student:
            student = User(
                email=email,
                password_hash=generate_password_hash('123456'),
                name=name,
                role='student'
            )
            db.session.add(student)
    
    db.session.commit()
    students = User.query.filter(User.role == 'student').all()
    print(f'✓ {len(students)} estudantes criados/verificados')

    # ============================================
    # CRIAÇÃO DE TURMAS
    # ============================================
    
    if Class.query.count() == 0:
        classes_data = [
            ('Introdução à Programação', 'Conceitos básicos de programação em Python', 'Segunda e Quarta, 19h-21h'),
            ('Estrutura de Dados', 'Algoritmos e estruturas de dados avançadas', 'Terça e Quinta, 18h-20h'),
            ('Interface Humano-Computador', 'Design de interfaces e experiência do usuário', 'Sexta, 14h-18h'),
            ('Banco de Dados', 'Modelagem e administração de bancos de dados', 'Sábado, 8h-12h'),
            ('Engenharia de Software', 'Metodologias de desenvolvimento de software', 'Segunda e Quinta, 20h-22h'),
            ('Matemática Discreta', 'Lógica e matemática para computação', 'Terça e Sexta, 16h-18h')
        ]
        
        for i, (name, description, schedule) in enumerate(classes_data):
            professor = professors[i % len(professors)]
            class_obj = Class(
                name=name,
                description=description,
                instructor_id=professor.id,
                schedule=schedule,
                is_active=True
            )
            db.session.add(class_obj)
        
        db.session.commit()
        print('✓ Turmas de exemplo criadas')

    return User.query.filter_by(email='admin@admin.com').first(), professors, students


def create_enrollments(students):
    """Criar matrículas e solicitações"""
    print("\n📝 Criando matrículas...")
    
    classes = Class.query.all()
    
    # Limpar matrículas existentes para recriar
    try:
        ClassEnrollment.query.delete()
        db.session.commit()
    except Exception as e:
        print(f"⚠️ Erro ao limpar matrículas: {e}")
        db.session.rollback()
    
    # Criar matrículas aprovadas
    for student in students[:5]:  # Primeiros 5 alunos já matriculados
        # Garantir que não tentamos selecionar mais turmas do que existem
        max_classes = min(len(classes), 4)
        min_classes = min(2, max_classes)
        num_classes = random.randint(min_classes, max_classes)
        selected_classes = random.sample(classes, num_classes)
        for class_obj in selected_classes:
            enrollment = ClassEnrollment(
                class_id=class_obj.id,
                student_id=student.id,
                status='approved'
            )
            db.session.add(enrollment)
    
    # Criar solicitações pendentes
    for student in students[5:]:  # Últimos 3 alunos com solicitações pendentes
        # Garantir que não tentamos selecionar mais turmas do que existem
        max_classes = min(len(classes), 3)
        min_classes = min(1, max_classes)
        num_classes = random.randint(min_classes, max_classes)
        selected_classes = random.sample(classes, num_classes)
        for class_obj in selected_classes:
            enrollment = ClassEnrollment(
                class_id=class_obj.id,
                student_id=student.id,
                status='pending'
            )
            db.session.add(enrollment)
    
    try:
        db.session.commit()
        print('✓ Matrículas e solicitações criadas')
    except Exception as e:
        print(f"⚠️ Erro ao criar matrículas: {e}")
        db.session.rollback()


def create_questions(admin, professors):
    """Criar questões do banco de dados"""
    print("\n❓ Criando questões do banco...")
    
    # Verificar se as novas colunas existem
    has_new_columns = (
        check_column_exists('questions', 'is_public') and
        check_column_exists('questions', 'created_by') and
        check_column_exists('questions', 'category') and
        check_column_exists('questions', 'difficulty')
    )
    
    # Limpar questões antigas do banco (que não estão em provas)
    try:
        # Primeiro deletar alternativas das questões do banco
        questions_to_delete = db.session.query(Question.id).filter(Question.exam_id.is_(None)).all()
        question_ids = [q.id for q in questions_to_delete]
        
        if question_ids:
            Alternative.query.filter(Alternative.question_id.in_(question_ids)).delete(synchronize_session=False)
            Question.query.filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
            db.session.commit()
            print("✓ Questões antigas do banco removidas")
    except Exception as e:
        print(f"⚠️ Erro ao limpar questões antigas: {e}")
        db.session.rollback()
    
    questions_data = [
        # Questões de Escolha Única
        {
            'question_text': 'Qual é a complexidade de tempo do algoritmo QuickSort no melhor caso?',
            'question_type': 'single_choice',
            'category': 'Algoritmos',
            'difficulty': 'medium',
            'is_public': True,
            'alternatives': [
                {'text': 'O(n)', 'is_correct': False},
                {'text': 'O(n log n)', 'is_correct': True},
                {'text': 'O(n²)', 'is_correct': False},
                {'text': 'O(log n)', 'is_correct': False}
            ]
        },
        {
            'question_text': 'Qual estrutura de dados segue o princípio LIFO?',
            'question_type': 'single_choice',
            'category': 'Estrutura de Dados',
            'difficulty': 'easy',
            'is_public': True,
            'alternatives': [
                {'text': 'Fila', 'is_correct': False},
                {'text': 'Pilha', 'is_correct': True},
                {'text': 'Lista', 'is_correct': False},
                {'text': 'Árvore', 'is_correct': False}
            ]
        },
        {
            'question_text': 'Em que ano foi criada a linguagem Python?',
            'question_type': 'single_choice',
            'category': 'Programação',
            'difficulty': 'easy',
            'is_public': True,
            'alternatives': [
                {'text': '1989', 'is_correct': False},
                {'text': '1991', 'is_correct': True},
                {'text': '1995', 'is_correct': False},
                {'text': '1999', 'is_correct': False}
            ]
        },
        # Questões de Múltipla Escolha
        {
            'question_text': 'Quais dos seguintes são princípios da programação orientada a objetos? (Selecione todas as corretas)',
            'question_type': 'multiple_choice',
            'category': 'Programação',
            'difficulty': 'medium',
            'is_public': True,
            'alternatives': [
                {'text': 'Encapsulamento', 'is_correct': True},
                {'text': 'Herança', 'is_correct': True},
                {'text': 'Polimorfismo', 'is_correct': True},
                {'text': 'Compilação', 'is_correct': False}
            ]
        },
        {
            'question_text': 'Quais das seguintes são características de bancos NoSQL?',
            'question_type': 'multiple_choice',
            'category': 'Banco de Dados',
            'difficulty': 'hard',
            'is_public': True,
            'alternatives': [
                {'text': 'Escalabilidade horizontal', 'is_correct': True},
                {'text': 'Schema flexível', 'is_correct': True},
                {'text': 'ACID garantido', 'is_correct': False},
                {'text': 'BASE consistency', 'is_correct': True}
            ]
        },
        # Questões Verdadeiro/Falso
        {
            'question_text': 'Python é uma linguagem de programação interpretada.',
            'question_type': 'true_false',
            'category': 'Programação',
            'difficulty': 'easy',
            'is_public': True,
            'alternatives': [
                {'text': 'Verdadeiro', 'is_correct': True},
                {'text': 'Falso', 'is_correct': False}
            ]
        },
        {
            'question_text': 'O algoritmo de ordenação Bubble Sort tem complexidade O(n log n) no pior caso.',
            'question_type': 'true_false',
            'category': 'Algoritmos',
            'difficulty': 'medium',
            'is_public': True,
            'alternatives': [
                {'text': 'Verdadeiro', 'is_correct': False},
                {'text': 'Falso', 'is_correct': True}
            ]
        },
        {
            'question_text': 'SQL é uma linguagem de consulta padrão para bancos relacionais.',
            'question_type': 'true_false',
            'category': 'Banco de Dados',
            'difficulty': 'easy',
            'is_public': True,
            'alternatives': [
                {'text': 'Verdadeiro', 'is_correct': True},
                {'text': 'Falso', 'is_correct': False}
            ]
        },
        # Questões Dissertativas
        {
            'question_text': 'Explique o conceito de programação orientada a objetos e cite os três pilares fundamentais com exemplos práticos.',
            'question_type': 'essay',
            'category': 'Programação',
            'difficulty': 'medium',
            'is_public': True,
            'alternatives': []
        },
        {
            'question_text': 'Compare e contraste as metodologias ágeis Scrum e Kanban, destacando vantagens e desvantagens de cada uma.',
            'question_type': 'essay',
            'category': 'Engenharia de Software',
            'difficulty': 'hard',
            'is_public': True,
            'alternatives': []
        },
        {
            'question_text': 'Descreva os princípios de usabilidade de Jakob Nielsen e como aplicá-los no design de interfaces web modernas.',
            'question_type': 'essay',
            'category': 'IHC',
            'difficulty': 'hard',
            'is_public': False,  # Questão privada
            'alternatives': []
        },
        {
            'question_text': 'Analise as diferenças entre bancos relacionais e não-relacionais, apresentando cenários de uso adequados para cada tipo.',
            'question_type': 'essay',
            'category': 'Banco de Dados',
            'difficulty': 'hard',
            'is_public': True,
            'alternatives': []
        }
    ]
    
    created_count = 0
    for question_data in questions_data:
        try:
            # Selecionar professor aleatório como criador
            creator = random.choice(professors + [admin])
            
            # Criar questão com ou sem novas colunas
            if has_new_columns:
                question = Question(
                    created_by=creator.id,
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    points=random.choice([1.0, 1.5, 2.0, 2.5, 3.0]),
                    category=question_data['category'],
                    difficulty=question_data['difficulty'],
                    is_public=question_data['is_public']
                )
            else:
                question = Question(
                    question_text=question_data['question_text'],
                    question_type=question_data['question_type'],
                    points=random.choice([1.0, 1.5, 2.0, 2.5, 3.0])
                )
            
            db.session.add(question)
            db.session.flush()  # Para obter o ID
            
            # Adicionar alternativas para questões objetivas
            for i, alt_data in enumerate(question_data['alternatives']):
                alternative = Alternative(
                    question_id=question.id,
                    alternative_text=alt_data['text'],
                    is_correct=alt_data['is_correct'],
                    order_number=i + 1
                )
                db.session.add(alternative)
            
            created_count += 1
            
        except Exception as e:
            print(f"⚠️ Erro ao criar questão '{question_data['question_text'][:50]}...': {e}")
            db.session.rollback()
            continue
    
    try:
        db.session.commit()
        print(f'✓ {created_count} questões do banco criadas')
    except Exception as e:
        print(f"⚠️ Erro ao salvar questões: {e}")
        db.session.rollback()


def create_exams():
    """Criar provas de exemplo"""
    print("\n📝 Criando provas...")
    
    if Exam.query.count() == 0:
        classes = Class.query.all()
        exam_templates = [
            ('Prova 1', 'Primeira avaliação', 120, 'published'),
            ('Prova 2', 'Segunda avaliação', 90, 'draft'),
            ('Prova Final', 'Avaliação final', 180, 'published')
        ]
        
        for class_obj in classes:
            for i, (title, description, duration, status) in enumerate(exam_templates):
                start_time = datetime.now() + timedelta(days=i*7 + random.randint(1, 5))
                end_time = start_time + timedelta(minutes=duration)
                
                exam = Exam(
                    title=f'{title} - {class_obj.name}',
                    description=f'{description} da disciplina {class_obj.name}',
                    duration_minutes=duration,
                    start_time=start_time,
                    end_time=end_time,
                    created_by=class_obj.instructor_id,
                    class_id=class_obj.id,
                    status=status
                )
                db.session.add(exam)
        
        try:
            db.session.commit()
            print('✓ Provas de exemplo criadas')
        except Exception as e:
            print(f"⚠️ Erro ao criar provas: {e}")
            db.session.rollback()


def show_statistics():
    """Mostrar estatísticas finais"""
    print("\n" + "="*60)
    print("🎉 INICIALIZAÇÃO COMPLETA COM MIGRAÇÕES V3!")
    print("="*60)
    print(f"👥 Usuários criados:")
    print(f"   - Administradores: {User.query.filter_by(role='admin').count()}")
    print(f"   - Professores: {User.query.filter_by(role='professor').count()}")
    print(f"   - Estudantes: {User.query.filter_by(role='student').count()}")
    print(f"🏫 Turmas: {Class.query.count()}")
    print(f"📝 Provas: {Exam.query.count()}")
    
    # Estatísticas de questões com fallback
    try:
        total_questions = Question.query.filter(Question.exam_id.is_(None)).count()
        print(f"❓ Questões do banco: {total_questions}")
        
        if check_column_exists('questions', 'is_public'):
            public_questions = Question.query.filter(Question.exam_id.is_(None), Question.is_public == True).count()
            private_questions = total_questions - public_questions
            print(f"   - Públicas: {public_questions}")
            print(f"   - Privadas: {private_questions}")
        
        if check_column_exists('questions', 'question_type'):
            single_choice = Question.query.filter(Question.exam_id.is_(None), Question.question_type == 'single_choice').count()
            multiple_choice = Question.query.filter(Question.exam_id.is_(None), Question.question_type == 'multiple_choice').count()
            true_false = Question.query.filter(Question.exam_id.is_(None), Question.question_type == 'true_false').count()
            essay = Question.query.filter(Question.exam_id.is_(None), Question.question_type == 'essay').count()
            
            print(f"📊 Tipos de questões:")
            print(f"   - Escolha Única: {single_choice}")
            print(f"   - Múltipla Escolha: {multiple_choice}")
            print(f"   - Verdadeiro/Falso: {true_false}")
            print(f"   - Dissertativas: {essay}")
        
    except Exception as e:
        print(f"⚠️ Erro ao calcular estatísticas de questões: {e}")
    
    try:
        print(f"✅ Matrículas aprovadas: {ClassEnrollment.query.filter_by(status='approved').count()}")
        print(f"⏳ Solicitações pendentes: {ClassEnrollment.query.filter_by(status='pending').count()}")
    except Exception as e:
        print(f"⚠️ Erro ao calcular estatísticas de matrículas: {e}")
    
    print("\n🔑 CREDENCIAIS DE ACESSO:")
    print("   Admin: admin@admin.com / admin123")
    print("   Professor: prof1@ufpi.edu.br / 123456")
    print("   Estudante: aluno1@ufpi.edu.br / 123456")
    print("\n🆕 NOVIDADES v3:")
    print("   ✓ Novos tipos de questões (Única, Múltipla, V/F, Dissertativa)")
    print("   ✓ Sistema de visibilidade (Pública/Privada)")
    print("   ✓ Pontuação específica por prova")
    print("   ✓ Histórico de questões em provas")
    print("   ✓ Função de recálculo de notas")
    print("="*60)


def init_db():
    """Função principal de inicialização"""
    app = create_app()
    with app.app_context():
        # Verificar schema do banco
        try:
            from sqlalchemy import text
            result = db.session.execute(text("SELECT class_id FROM exams LIMIT 1"))
            print("✓ Schema do banco verificado")
        except Exception as e:
            print(f"⚠️ Schema desatualizado: {e}")
            print("🔄 Recriando todas as tabelas...")
            db.drop_all()
        
        # Criar as tabelas
        db.create_all()
        print("✓ Tabelas criadas/verificadas")

        # Aplicar migrações para novas funcionalidades
        apply_migrations()

        # Criar dados básicos
        admin, professors, students = create_basic_data()

        # Criar matrículas
        create_enrollments(students)

        # Criar questões do banco
        create_questions(admin, professors)

        # Criar provas
        create_exams()

        # Mostrar estatísticas
        show_statistics()


if __name__ == '__main__':
    init_db() 