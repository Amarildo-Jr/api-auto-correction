FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (cache layer separado)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar APENAS requirements.txt primeiro (para cache de dependências)
COPY requirements.txt .

# Instalar dependências Python (cache layer)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação (depois das dependências)
COPY . .

# Expor a porta da aplicação
EXPOSE 5000

# Dar permissão de execução ao entrypoint
RUN chmod +x /app/entrypoint.sh

# Comando para iniciar usando o entrypoint completo
CMD ["/app/entrypoint.sh"] 