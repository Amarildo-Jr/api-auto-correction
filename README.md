# API de Sistema de Provas Online

API simples desenvolvida com Flask e PostgreSQL para sistema de provas online.

## 🚀 Execução

**Um único comando:**

```bash
docker-compose up --build
```

✅ **Pronto!** PostgreSQL + API Flask criados automaticamente.

- 🌐 **API:** http://localhost:5000
- 📊 **Banco:** postgresql://postgres:postgres@localhost:5432/exam_db  
- 👤 **Login:** admin@admin.com / admin123

## 📁 Estrutura

```
api/
├── app.py           # Aplicação Flask principal
├── models.py        # Modelos do banco de dados
├── routes.py        # Rotas da API
├── database.py      # Configuração do SQLAlchemy
├── init_db.py       # Script de inicialização do banco
├── requirements.txt # Dependências
└── Dockerfile       # Container da API
```

## 🌐 Endpoints Principais

### Autenticação
- `POST /api/auth/login` - Login

### Usuários  
- `POST /api/users` - Criar usuário
- `GET /api/users/me` - Dados do usuário atual

### Provas
- `GET /api/exams` - Listar provas
- `POST /api/exams` - Criar prova
- `GET /api/exams/<id>` - Detalhes da prova
- `POST /api/exams/<id>/questions` - Adicionar questão

### Realização
- `POST /api/exams/<id>/start` - Iniciar prova
- `POST /api/enrollments/<id>/submit-answer` - Submeter resposta
- `POST /api/enrollments/<id>/finish` - Finalizar prova

### Teste
- `GET /api/test` - Healthcheck

## 🔑 Credenciais Iniciais

- **Email:** admin@admin.com
- **Senha:** admin123

## 🗄️ Banco de Dados

- **Host:** localhost
- **Porta:** 5432
- **Usuário:** postgres
- **Senha:** postgres
- **Database:** exam_db

### Tabelas criadas automaticamente:
- users, exams, questions, alternatives
- exam_enrollments, answers, monitoring_events

## 📝 Exemplo de Uso

```bash
# 1. Iniciar tudo
docker-compose up --build

# 2. Fazer login (em outro terminal)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin123"}'

# 3. Testar API
curl http://localhost:5000/api/test
``` 