# API UFPI IC - Sistema de Correção Automática

Esta é a API backend do sistema de provas online com correção automática da UFPI IC.

## 🚀 Inicialização Rápida

### Opção 1: Script Automatizado (Recomendado)
```bash
cd api
./start-api.sh
```

### Opção 2: Docker Compose Direto
```bash
cd api
docker compose up --build
```

### Opção 3: Desenvolvimento Local
```bash
cd api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python app.py
```

## 📁 Estrutura do Projeto

```
api/
├── docker-compose.yml       # Configuração Docker (API + PostgreSQL)
├── env.example             # Template de variáveis de ambiente
├── start-api.sh            # Script de inicialização
├── generate_jwt_secret.py   # Gerador de JWT Secret Key
├── Dockerfile              # Imagem Docker da API
├── requirements.txt        # Dependências Python
├── app.py                  # Aplicação Flask principal
├── models.py               # Modelos do banco de dados
├── routes.py               # Rotas da API
├── database.py             # Configuração do banco
├── auto_correction.py      # Sistema de correção automática
├── test_auto_correction.py # Testes da correção automática
├── migrate.py              # Script de migração
└── init_db.py              # Inicialização do banco
```

## 🐳 Docker

A API agora tem seu próprio `docker-compose.yml` que inclui:
- **PostgreSQL**: Banco de dados
- **Flask API**: Aplicação backend

### Comandos Docker
```bash
# Iniciar API + Banco
docker compose up --build

# Parar serviços
docker compose down

# Ver logs
docker compose logs -f

# Reiniciar apenas a API
docker compose restart api
```

## 🔧 Configuração

### 1. Variáveis de Ambiente
Copie o arquivo de exemplo:
```bash
cp env.example .env
```

### 2. Google AI API Key (Para Correção Automática)
```bash
# Edite .env e adicione:
GOOGLE_GENAI_API_KEY=sua_chave_aqui
```

**Como obter a chave:**
1. Acesse https://aistudio.google.com/
2. Faça login com conta Google
3. Vá em "Get API Key" > "Create API Key"
4. Copie a chave gerada

### 3. JWT Secret Key
É gerada automaticamente pelo script `start-api.sh`. Para gerar manualmente:
```bash
python generate_jwt_secret.py
```

## 🧪 Sistema de Correção Automática

### Como Funciona
1. **Professor** cria questão com gabarito esperado
2. **Estudante** responde a questão
3. **IA** compara resposta com gabarito usando similaridade semântica
4. **Sistema** atribui pontuação automática
5. **Professor** pode revisar e ajustar correções

### Tecnologia Utilizada
- **Google Generative AI** (Gemini 1.5 Flash)
- **Análise semântica** de texto
- **Pontuação proporcional** (0-10)

### Exemplo de Uso
```python
from auto_correction import auto_correction

# Resposta esperada (gabarito)
teacher_answer = "A fotossíntese é o processo pelo qual as plantas convertem luz solar em energia química."

# Resposta do estudante
student_answer = "As plantas usam luz do sol para fazer comida através da fotossíntese."

# Correção automática
points, similarity = auto_correction.auto_correct_essay(
    teacher_answer, 
    student_answer, 
    max_points=10.0
)

print(f"Pontos: {points}/10.0")
print(f"Similaridade: {similarity}/10.0")
```

### Testar Correção Automática
```bash
python test_auto_correction.py
```

## 📡 Endpoints da API

### Autenticação
- `POST /api/auth/login` - Login de usuário
- `POST /api/auth/register` - Registro de usuário

### Questões (Professor)
- `GET /api/teacher/questions` - Listar questões
- `POST /api/teacher/questions` - Criar questão
- `PUT /api/teacher/questions/{id}` - Editar questão
- `DELETE /api/teacher/questions/{id}` - Deletar questão

### Provas
- `GET /api/teacher/exams` - Listar provas
- `POST /api/teacher/exams` - Criar prova
- `POST /api/student/exams/{id}/submit` - Finalizar prova

### Correção Automática
- `POST /api/teacher/auto-correction` - Corrigir questão
- `GET /api/teacher/results/pending-corrections` - Correções pendentes
- `POST /api/teacher/results/manual-correction` - Correção manual

### Status
- `GET /api/health` - Status da API

## 🗄️ Banco de Dados

### Migração
```bash
python migrate.py
```

### Inicialização (primeira vez)
```bash
python init_db.py
```

### Conexão
```
Host: localhost
Port: 5432
Database: ufpi_ic
User: postgres
Password: postgres123
```

## 🔧 Desenvolvimento

### Instalar Dependências
```bash
pip install -r requirements.txt
```

### Executar Testes
```bash
python test_auto_correction.py
```

### Adicionar Nova Dependência
```bash
pip install nova_dependencia
pip freeze > requirements.txt
```

### Debug
```bash
export FLASK_DEBUG=true
python app.py
```

## 📊 Monitoramento

### Logs da API
```bash
docker compose logs -f api
```

### Status dos Serviços
```bash
docker compose ps
```

### Recursos do Sistema
```bash
docker stats
```

## 🚨 Solução de Problemas

### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
docker compose ps

# Reiniciar banco
docker compose restart postgres
```

### Erro de Correção Automática
```bash
# Verificar chave da API
grep GOOGLE_GENAI_API_KEY docker.env

# Testar correção
python test_auto_correction.py
```

### Erro de Permissão
```bash
# Linux/Mac
chmod +x start-api.sh

# Windows (PowerShell)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Limpar Cache Docker
```bash
docker system prune -a --volumes
```

## 📚 Documentação Adicional

- `CONFIGURACAO_CORRECAO_AUTOMATICA.md` - Guia completo da correção automática
- `generate_jwt_secret.py` - Gerador de chaves JWT
- Logs de desenvolvimento em `docker compose logs -f`

## 🆘 Suporte

Em caso de problemas:
1. Verifique os logs: `docker compose logs -f`
2. Execute os testes: `python test_auto_correction.py`
3. Consulte a documentação
4. Reinicie os serviços: `docker compose restart` 