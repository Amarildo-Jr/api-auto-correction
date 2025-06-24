# 🐳 Deploy da API no Render usando Docker

Este guia te ajudará a fazer o deploy da API usando Docker no Render, com banco PostgreSQL gerenciado separadamente.

## 🏗️ Arquitetura

- **API**: Container Docker no Render Web Service
- **Banco**: PostgreSQL gerenciado pelo Render (separado)
- **Vantagens**: Isolamento, controle total do ambiente, fácil replicação

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com)
2. Repositório Git com o código da API
3. Docker configurado localmente (para testes)
4. Chave do Google Generative AI ([obter aqui](https://aistudio.google.com/))

## 🗄️ Passo 1: Criar o Banco PostgreSQL

1. No painel do Render, clique em **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `ufpi-ic-postgres`
   - **Database**: `ufpi_ic`
   - **User**: `postgres`
   - **Region**: escolha a mais próxima
   - **Plan**: Free

4. Clique em **"Create Database"**
5. **Anote a DATABASE_URL** (ex: `postgresql://user:pass@host:port/ufpi_ic`)

## 🔧 Passo 2: Preparar Variáveis de Ambiente

Gere uma chave JWT forte:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🐳 Passo 3: Criar o Web Service (Docker)

1. No painel do Render, clique em **"New +"**
2. Selecione **"Web Service"**
3. Conecte seu repositório Git
4. Configure:
   - **Name**: `ufpi-ic-api`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
   - **Plan**: Free

## ⚙️ Passo 4: Configurar Variáveis de Ambiente

No painel do Web Service, vá em **"Environment"** e adicione:

```bash
# Ambiente
FLASK_ENV=production

# Porta (Render define automaticamente)
PORT=10000

# JWT (use a chave que você gerou)
JWT_SECRET_KEY=sua-chave-jwt-forte-aqui

# Google AI
GOOGLE_GENAI_API_KEY=sua-chave-google-ai-aqui

# CORS (domínio do seu frontend)
CORS_ORIGINS=https://seu-frontend.netlify.app

# Database (copie do PostgreSQL criado)
DATABASE_URL=postgresql://user:pass@host:port/ufpi_ic
```

## 🔗 Passo 5: Conectar o Banco

**Opção A - Manual:**
1. Copie a `DATABASE_URL` do banco PostgreSQL
2. Cole nas variáveis de ambiente do Web Service

**Opção B - Automática:**
1. No Web Service, vá em **"Environment"**
2. Clique em **"Add from Database"**
3. Selecione o banco `ufpi-ic-postgres`

## 🚀 Passo 6: Deploy

1. Clique em **"Create Web Service"**
2. O Render irá:
   - Fazer build da imagem Docker
   - Executar o container
   - Expor na porta configurada

3. Acompanhe os logs durante o deploy

## 📊 Passo 7: Inicializar o Banco

Após o primeiro deploy bem-sucedido:

1. No painel do Web Service, vá em **"Shell"**
2. Execute:
```bash
python init_render_db.py
```

## ✅ Passo 8: Testar a API

1. Acesse: `https://ufpi-ic-api.onrender.com`
2. Teste health check: `GET /health`
3. Deve retornar:
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

## 🛠️ Desenvolvimento Local

Para testar localmente com Docker:

```bash
# Com banco PostgreSQL no Docker (desenvolvimento)
docker-compose -f docker-compose.dev.yml up --build

# Apenas a API (conectando com banco externo)
docker-compose up --build
```

## 🔄 Atualizações e Manutenção

### Deploy de Atualizações
1. Faça push para o repositório Git
2. Render fará rebuild automático da imagem
3. Deploy automático do novo container

### Monitoramento
- **Logs**: Painel do Render > Logs
- **Métricas**: Painel do Render > Metrics
- **Health Check**: `/health` endpoint

### Backup do Banco
1. No painel do PostgreSQL
2. Vá em "Backups"
3. Configure backups automáticos

## 🐛 Troubleshooting

### Container não inicia
```bash
# Verificar logs no painel do Render
# Testar localmente:
docker build -t ufpi-api .
docker run -p 5000:5000 --env-file .env ufpi-api
```

### Erro de conexão com banco
```bash
# Verificar DATABASE_URL
# Testar conexão:
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print('Conexão OK!' if engine.connect() else 'Erro!')
"
```

### Problemas de CORS
```bash
# Verificar CORS_ORIGINS
# Testar com curl:
curl -H "Origin: https://seu-frontend.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://ufpi-ic-api.onrender.com/api/auth/login
```

## 📊 Comparação: Docker vs Python Native

| Aspecto | Docker | Python Native |
|---------|--------|---------------|
| **Controle** | Total | Limitado |
| **Dependências** | Isoladas | Compartilhadas |
| **Build Time** | Mais lento | Mais rápido |
| **Debugging** | Mais complexo | Mais simples |
| **Portabilidade** | Máxima | Boa |

## 🎯 Próximos Passos

1. ✅ API funcionando no Render
2. 🔧 Configure monitoramento
3. 🔒 Configure backups do banco
4. 🚀 Configure CI/CD se necessário
5. 📱 Conecte o frontend

---

🎉 **Pronto!** Sua API está rodando em container Docker no Render com PostgreSQL separado! 