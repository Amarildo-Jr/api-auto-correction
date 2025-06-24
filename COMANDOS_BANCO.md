# 🛠️ Comandos Úteis para Gerenciar o Banco

## 🔧 Scripts Disponíveis

### 1. Testar Conexão
```bash
python test_database_connection.py
```
- Verifica se a conexão com o banco está funcionando
- Mostra informações sobre tabelas e dados
- Útil para diagnóstico

### 2. Inicializar Banco (Primeira vez)
```bash
python init_render_db.py
```
- Cria todas as tabelas
- Adiciona usuário admin padrão
- Adiciona dados de exemplo

### 3. Migração de Banco
```bash
python migrate.py
```
- Aplica mudanças na estrutura do banco
- Use quando houver alterações nos modelos

## 🗄️ Comandos PostgreSQL (psql)

### Conectar ao banco
```bash
# No shell do Render
psql $DATABASE_URL

# Localmente (se tiver psql instalado)
psql "postgresql://user:pass@host:port/database"
```

### Comandos básicos
```sql
-- Listar bancos de dados
\l

-- Conectar a um banco específico
\c ufpi_ic

-- Listar tabelas
\dt

-- Descrever estrutura de uma tabela
\d users
\d questions
\d exams

-- Sair do psql
\q
```

### Consultas úteis
```sql
-- Ver todos os usuários
SELECT id, username, email, role, is_active, created_at 
FROM users 
ORDER BY created_at DESC;

-- Contar registros por tabela
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL
SELECT 'classes', COUNT(*) FROM classes
UNION ALL
SELECT 'questions', COUNT(*) FROM questions
UNION ALL
SELECT 'exams', COUNT(*) FROM exams
UNION ALL
SELECT 'answers', COUNT(*) FROM answers;

-- Ver matérias cadastradas
SELECT id, name, description, created_at 
FROM subjects 
ORDER BY name;

-- Ver turmas ativas
SELECT c.id, c.name, s.name as subject_name, u.username as teacher
FROM classes c
JOIN subjects s ON c.subject_id = s.id
JOIN users u ON c.teacher_id = u.id
WHERE c.is_active = true;

-- Ver exames recentes
SELECT e.id, e.title, c.name as class_name, e.created_at
FROM exams e
JOIN classes c ON e.class_id = c.id
ORDER BY e.created_at DESC
LIMIT 10;
```

## 🔧 Manutenção do Banco

### Backup Manual
```sql
-- Exportar dados de uma tabela
COPY users TO '/tmp/users_backup.csv' DELIMITER ',' CSV HEADER;

-- Importar dados
COPY users FROM '/tmp/users_backup.csv' DELIMITER ',' CSV HEADER;
```

### Limpeza de Dados
```sql
-- Remover exames antigos (exemplo: mais de 1 ano)
DELETE FROM exams 
WHERE created_at < NOW() - INTERVAL '1 year';

-- Remover respostas órfãs
DELETE FROM answers 
WHERE exam_id NOT IN (SELECT id FROM exams);

-- Vacuum para otimizar espaço
VACUUM ANALYZE;
```

### Índices para Performance
```sql
-- Adicionar índices úteis
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_answers_exam_id ON answers(exam_id);
CREATE INDEX idx_questions_class_id ON questions(class_id);
CREATE INDEX idx_exams_created_at ON exams(created_at);

-- Ver índices existentes
\di
```

## 🔍 Monitoramento

### Verificar conexões ativas
```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE state = 'active';
```

### Verificar tamanho das tabelas
```sql
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;
```

### Estatísticas do banco
```sql
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables;
```

## 🚨 Resolução de Problemas

### Resetar senha do admin
```sql
-- Atualizar senha do admin (hash para 'novasenha123')
UPDATE users 
SET password_hash = 'pbkdf2:sha256:600000$...' 
WHERE email = 'admin@ufpi.edu.br';
```

### Recriar tabelas (CUIDADO!)
```sql
-- ATENÇÃO: Isso apaga todos os dados!
DROP TABLE IF EXISTS answers CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Depois execute: python init_render_db.py
```

### Verificar integridade
```sql
-- Verificar chaves estrangeiras
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## 📊 Scripts Python Úteis

### Contar registros
```python
from app import create_app
from database import db
from models import User, Subject, Class, Question, Exam, Answer

app = create_app('production')
with app.app_context():
    print(f"Usuários: {User.query.count()}")
    print(f"Matérias: {Subject.query.count()}")
    print(f"Turmas: {Class.query.count()}")
    print(f"Questões: {Question.query.count()}")
    print(f"Exames: {Exam.query.count()}")
    print(f"Respostas: {Answer.query.count()}")
```

### Criar usuário admin
```python
from app import create_app
from database import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    admin = User(
        username='admin',
        email='admin@ufpi.edu.br',
        password_hash=generate_password_hash('senha123'),
        role='admin',
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin criado!")
```

## 🎯 Comandos Rápidos

```bash
# Testar tudo
python test_database_connection.py

# Inicializar banco
python init_render_db.py

# Conectar via psql
psql $DATABASE_URL

# Ver logs da API
# (no painel do Render)

# Verificar health
curl https://sua-api.onrender.com/health
```

---

💡 **Dica**: Sempre faça backup antes de executar comandos que modificam dados! 