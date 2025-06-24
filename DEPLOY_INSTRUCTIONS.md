# 🚀 Instruções de Deploy no Render

## ✅ Alterações Realizadas

As seguintes alterações foram feitas para corrigir o problema de deploy:

### 1. Configuração do Banco de Dados
- **Nome do serviço**: `db-auto-correction` (em vez de ufpi-ic-postgres)
- **Nome do banco**: `auto_correction` (em vez de ufpi_ic)
- **Usuário**: removido do render.yaml (Render gerará automaticamente)

### 2. Arquivos Atualizados
- ✅ `render.yaml` - Configuração principal do deploy
- ✅ `config.py` - Nome do banco local atualizado
- ✅ `env.example` - URL do banco atualizada
- ✅ `docker-compose.dev.yml` - Nomes dos containers e banco atualizados
- ✅ `docker-compose.yml` - Nome do container atualizado
- ✅ `entrypoint.sh` - Nome do banco atualizado
- ✅ `README.md` - Referências ao nome do banco atualizadas

### 3. Arquivos Removidos
- ❌ `COMANDOS_BANCO.md` - Instruções obsoletas
- ❌ `CONFIGURAR_BANCO_RENDER.md` - Redundante com render.yaml
- ❌ `DEPLOY_RENDER_DOCKER.md` - Instruções desnecessárias
- ❌ `DEPLOY_RENDER.md` - Substituído por este arquivo

## 🗄️ Deploy do Banco de Dados

1. **No Render Dashboard:**
   - O arquivo `render.yaml` criará automaticamente o banco `db-auto-correction`
   - Nome do banco: `auto_correction`
   - O Render gerará usuário e senha automaticamente

2. **Variáveis Criadas Automaticamente:**
   - `DATABASE_URL`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_DB`
   - `POSTGRES_HOST`
   - `POSTGRES_PORT`

## 🔧 Variáveis de Ambiente Necessárias

Configure no painel do Render:

```bash
# JWT Secret (gere uma chave forte)
JWT_SECRET_KEY=sua-chave-jwt-aqui

# Google AI API Key
GOOGLE_GENAI_API_KEY=sua-chave-google-ai-aqui

# CORS Origins (domínio do frontend)
CORS_ORIGINS=https://seu-frontend.com
```

## 📊 Após o Deploy

1. **Inicializar o banco:**
   ```bash
   python init_render_db.py
   ```

2. **Testar a conexão:**
   ```bash
   python test_database_connection.py
   ```

3. **Verificar health check:**
   ```
   GET https://auto-correction-api.onrender.com/health
   ```

## 🔐 Dados Padrão Criados

- **Admin:** admin@ufpi.edu.br / admin123
- **Matérias:** Matemática, Português, História, Geografia

⚠️ **IMPORTANTE:** Altere a senha do admin após o primeiro login!

## 🐛 Troubleshooting

- **Erro "user must not be postgres"**: ✅ Corrigido removendo a linha `user` do render.yaml
- **Erro de conexão**: Verifique se DATABASE_URL foi configurada automaticamente
- **Erro 500**: Verifique logs no painel do Render

---

🎉 **Deploy configurado corretamente!** Agora você pode fazer o deploy usando o arquivo `render.yaml`. 