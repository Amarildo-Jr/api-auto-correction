FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash app

# Copiar requirements.txt primeiro (para cache de dependências)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para logs e dar permissões
RUN mkdir -p /app/logs && \
    chown -R app:app /app

# Mudar para usuário não-root
USER app

# Expor porta (será definida via variável de ambiente)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Comando para iniciar a aplicação
CMD ["python", "app.py"] 