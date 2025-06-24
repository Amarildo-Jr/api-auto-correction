# 🚀 Deploy da API no Render

Este guia te ajudará a fazer o deploy da API no Render de forma separada do banco de dados.

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com)
2. Repositório Git com o código da API
3. Chave do Google Generative AI ([obter aqui](https://aistudio.google.com/))

## 🗄️ Passo 1: Criar o Banco PostgreSQL

1. No painel do Render, clique em **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `ufpi-ic-postgres` (ou outro nome)
   - **Database**: `ufpi_ic`
   - **User**: `postgres` (padrão)
   - **Region**: escolha a mais próxima
   - **PostgreSQL Version**: 15 (recomendado)
   - **Plan**: Free (para testes)

4. Clique em **"Create Database"**
5. **Anote a URL de conexão** que será mostrada (ex: `postgresql://user:pass@host:port/db`)

## 🔧 Passo 2: Preparar as Variáveis de Ambiente

Gere uma chave JWT forte:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🌐 Passo 3: Criar o Web Service

1. No painel do Render, clique em **"New +"**
2. Selecione **"Web Service"**
3. Conecte seu repositório Git
4. Configure:
   - **Name**: `ufpi-ic-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (para testes)

## ⚙️ Passo 4: Configurar Variáveis de Ambiente

No painel do Web Service, vá em **"Environment"** e adicione:

```bash
# Ambiente
FLASK_ENV=production

# JWT (use a chave que você gerou)
JWT_SECRET_KEY=sua-chave-jwt-forte-aqui

# Google AI (sua chave da API)
GOOGLE_GENAI_API_KEY=sua-chave-google-ai-aqui

# CORS (domínio do seu frontend - se houver)
CORS_ORIGINS=https://seu-frontend.netlify.app

# Database (copie do banco PostgreSQL criado)
DATABASE_URL=postgresql://user:pass@host:port/database
```

## 🔗 Passo 5: Conectar o Banco

1. No seu Web Service, vá em **"Environment"**
2. Clique em **"Add Environment Variable"**
3. Em **"Add from Database"**, selecione o banco PostgreSQL criado
4. Isso adicionará automaticamente a `DATABASE_URL`

## 🚀 Passo 6: Deploy

1. Clique em **"Create Web Service"**
2. O Render fará o build e deploy automaticamente
3. Aguarde o processo terminar (pode demorar alguns minutos)

## 📊 Passo 7: Inicializar o Banco

Após o primeiro deploy bem-sucedido:

1. No painel do Web Service, vá em **"Shell"**
2. Execute o comando:
```bash
python init_render_db.py
```

Este comando irá:
- Criar todas as tabelas
- Criar usuário admin padrão
- Adicionar matérias de exemplo

## ✅ Passo 8: Testar a API

1. Acesse a URL do seu serviço (ex: `https://ufpi-ic-api.onrender.com`)
2. Teste o health check: `GET /health`
3. Teste o login admin:
   - **Email**: `admin@ufpi.edu.br`
   - **Senha**: `admin123` (ALTERE IMEDIATAMENTE!)

## 🔒 Segurança Pós-Deploy

1. **Altere a senha do admin** após o primeiro login
2. **Configure CORS** adequadamente para seu frontend
3. **Use HTTPS** sempre (Render fornece automaticamente)
4. **Monitore os logs** no painel do Render

## 🔄 Atualizações

Para atualizar a API:
1. Faça push das mudanças para o repositório Git
2. O Render fará redeploy automaticamente
3. Para mudanças no banco, execute migrações se necessário

## 🐛 Troubleshooting

### Erro de Conexão com Banco
- Verifique se `DATABASE_URL` está correta
- Confirme que o banco PostgreSQL está rodando
- Teste a conexão no shell do Render

### Erro 500 na API
- Verifique os logs no painel do Render
- Confirme se todas as variáveis de ambiente estão configuradas
- Teste localmente primeiro

### Erro de CORS
- Configure `CORS_ORIGINS` com o domínio do frontend
- Use HTTPS nos domínios de produção

## 📱 Próximos Passos

Após a API estar funcionando:
1. Configure o frontend para usar a URL da API no Render
2. Teste todas as funcionalidades
3. Configure monitoramento e backups se necessário

---

🎉 **Parabéns!** Sua API está rodando no Render com banco PostgreSQL separado! 