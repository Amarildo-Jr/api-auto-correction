# 🗄️ Configuração do Banco PostgreSQL no Render

Este guia te mostra como configurar o banco PostgreSQL no Render e conectá-lo com sua API.

## 🚀 Passo 1: Criar o Banco PostgreSQL

### 1.1 No Painel do Render

1. Acesse [render.com](https://render.com) e faça login
2. No dashboard, clique em **"New +"**
3. Selecione **"PostgreSQL"**

### 1.2 Configurações do Banco

Preencha os campos:

```
Name: ufpi-ic-postgres
Database: ufpi_ic
User: postgres
Region: Ohio (US East) - ou mais próxima de você
PostgreSQL Version: 15
Plan: Free (para desenvolvimento/testes)
```

### 1.3 Criar o Banco

1. Clique em **"Create Database"**
2. Aguarde alguns minutos para a criação
3. **IMPORTANTE**: Anote as informações de conexão

## 📋 Passo 2: Obter Informações de Conexão

Após a criação, você verá as seguintes informações:

### 2.1 Informações Internas (para conexão da API)
```
Internal Database URL: postgresql://postgres:senha@dpg-xxx-a.ohio-postgres.render.com/ufpi_ic
Hostname: dpg-xxx-a.ohio-postgres.render.com
Port: 5432
Database: ufpi_ic
Username: postgres
Password: [senha gerada automaticamente]
```

### 2.2 Informações Externas (para acesso direto)
```
External Database URL: postgresql://postgres:senha@dpg-xxx-a.ohio-postgres.render.com:5432/ufpi_ic
```

## 🔗 Passo 3: Conectar com a API

### 3.1 Configurar Variáveis de Ambiente

No seu Web Service da API:

1. Vá em **"Environment"**
2. Adicione a variável:

```bash
DATABASE_URL=postgresql://postgres:senha@dpg-xxx-a.ohio-postgres.render.com/ufpi_ic
```

### 3.2 Conexão Automática (Recomendado)

1. No painel do Web Service da API
2. Vá em **"Environment"** 
3. Clique em **"Add Environment Variable"**
4. Selecione **"Add from Database"**
5. Escolha `ufpi-ic-postgres`
6. Isso adicionará automaticamente a `DATABASE_URL`

## 🛠️ Passo 4: Inicializar o Banco

### 4.1 Executar Script de Inicialização

Após o deploy da API:

1. No painel do Web Service, vá em **"Shell"**
2. Execute:

```bash
python init_render_db.py
```

### 4.2 O que o script faz:

- ✅ Cria todas as tabelas do banco
- ✅ Cria usuário administrador padrão
- ✅ Adiciona matérias de exemplo
- ✅ Configura dados iniciais

### 4.3 Dados Criados:

**Usuário Admin:**
- Email: `admin@ufpi.edu.br`
- Senha: `admin123` (ALTERE IMEDIATAMENTE!)
- Role: `admin`

**Matérias de Exemplo:**
- Matemática
- Português
- História
- Geografia

## 🔍 Passo 5: Verificar Conexão

### 5.1 Health Check

Acesse: `https://sua-api.onrender.com/health`

Deve retornar:
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

### 5.2 Teste de Login

```bash
curl -X POST https://sua-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ufpi.edu.br",
    "password": "admin123"
  }'
```

## 🛡️ Passo 6: Configurações de Segurança

### 6.1 Alterar Senha do Admin

1. Faça login na API
2. Use o endpoint de alteração de senha
3. Ou execute no shell:

```python
from app import create_app
from database import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    admin = User.query.filter_by(email='admin@ufpi.edu.br').first()
    admin.password_hash = generate_password_hash('nova_senha_forte')
    db.session.commit()
    print("Senha alterada com sucesso!")
```

### 6.2 Configurar SSL (Automático)

O Render configura automaticamente SSL para conexões com PostgreSQL.

## 📊 Passo 7: Monitoramento do Banco

### 7.1 No Painel do Render

- **Métricas**: CPU, Memória, Conexões
- **Logs**: Queries, Erros, Conexões
- **Backups**: Configurar backups automáticos

### 7.2 Configurar Backups

1. No painel do PostgreSQL
2. Vá em **"Backups"**
3. Configure:
   - Frequência: Diária
   - Retenção: 7 dias (plano free)

## 🔧 Passo 8: Gerenciar o Banco

### 8.1 Acesso Direto (psql)

```bash
# No shell do Web Service
psql $DATABASE_URL
```

### 8.2 Comandos Úteis

```sql
-- Listar tabelas
\dt

-- Ver estrutura de uma tabela
\d users

-- Contar registros
SELECT COUNT(*) FROM users;

-- Ver usuários
SELECT id, username, email, role FROM users;
```

### 8.3 Interface Gráfica

Use ferramentas como:
- **pgAdmin**
- **DBeaver**
- **TablePlus**

Conecte usando a External Database URL.

## 🚨 Troubleshooting

### Erro: "Could not connect to server"

**Causa**: DATABASE_URL incorreta ou banco não criado

**Solução**:
1. Verifique se o banco PostgreSQL está rodando
2. Confirme a DATABASE_URL
3. Teste conexão no shell

### Erro: "relation does not exist"

**Causa**: Tabelas não foram criadas

**Solução**:
```bash
python init_render_db.py
```

### Erro: "too many connections"

**Causa**: Limite de conexões do plano free (22 conexões)

**Solução**:
1. Configure connection pooling na API
2. Feche conexões não utilizadas
3. Considere upgrade do plano

### Performance Lenta

**Causa**: Plano free tem limitações

**Solução**:
1. Otimize queries
2. Adicione índices necessários
3. Considere upgrade para plano pago

## 📈 Limites do Plano Free

- **Storage**: 1GB
- **Conexões**: 22 simultâneas
- **Backup**: 7 dias de retenção
- **RAM**: 256MB
- **CPU**: Compartilhada

## 🔄 Migrações de Banco

### Para mudanças na estrutura:

1. Crie um script de migração
2. Execute no shell do Render:

```bash
python migrate.py
```

### Exemplo de migração:

```python
# migrate.py
from app import create_app
from database import db

app = create_app('production')
with app.app_context():
    # Adicionar nova coluna
    db.engine.execute("ALTER TABLE questions ADD COLUMN new_field TEXT;")
    print("Migração executada!")
```

## 🎯 Próximos Passos

1. ✅ Banco PostgreSQL criado e configurado
2. ✅ API conectada ao banco
3. ✅ Dados iniciais criados
4. 🔄 Configurar backups
5. 🔒 Alterar senha padrão
6. 📊 Monitorar performance

---

🎉 **Pronto!** Seu banco PostgreSQL está configurado e conectado com a API no Render! 