FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de requisitos e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta da aplicação
EXPOSE 5000

# Criar um script de inicialização robusto
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Aguardando banco de dados..."\n\
\n\
# Função para verificar conexão com o banco\n\
wait_for_db() {\n\
    local max_attempts=30\n\
    local attempt=1\n\
    \n\
    while [ $attempt -le $max_attempts ]; do\n\
        echo "Tentativa $attempt/$max_attempts de conexão com o banco..."\n\
        \n\
        if python -c "from database import db; from app import app; app.app_context().push(); db.engine.connect()" 2>/dev/null; then\n\
            echo "✅ Conectado ao banco com sucesso!"\n\
            return 0\n\
        fi\n\
        \n\
        echo "❌ Falha na conexão. Aguardando 2 segundos..."\n\
        sleep 2\n\
        attempt=$((attempt + 1))\n\
    done\n\
    \n\
    echo "❌ Não foi possível conectar ao banco após $max_attempts tentativas."\n\
    exit 1\n\
}\n\
\n\
# Aguardar conexão com o banco\n\
wait_for_db\n\
\n\
echo "📊 Inicializando o banco de dados..."\n\
if python init_db.py; then\n\
    echo "✅ Banco de dados inicializado com sucesso!"\n\
else\n\
    echo "❌ Erro ao inicializar banco de dados."\n\
    exit 1\n\
fi\n\
\n\
echo "🌟 Iniciando a aplicação Flask..."\n\
exec python app.py' > /app/start.sh

# Dar permissão de execução ao script
RUN chmod +x /app/start.sh

# Comando para iniciar com o script de inicialização
CMD ["/app/start.sh"] 