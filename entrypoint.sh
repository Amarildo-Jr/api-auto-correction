#!/bin/bash
set -e

echo "🚀 Verificando conexão com PostgreSQL..."

# Verificar se DATABASE_URL está configurada (Render)
if [ -n "$DATABASE_URL" ]; then
  echo "✅ DATABASE_URL encontrada, usando banco do Render"
  
  # Testar conexão com o banco do Render
  for i in {1..10}; do
    if python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    conn.close()
    print('Conexão OK')
    exit(0)
except Exception as e:
    exit(1)
" 2>/dev/null; then
      echo "✅ PostgreSQL do Render conectado!"
      break
    fi
    echo "Tentativa $i/10... Aguardando PostgreSQL do Render"
    sleep 3
  done
else
  # Ambiente local - aguardar PostgreSQL local
  echo "🏠 Ambiente local detectado"
  for i in {1..30}; do
    if python -c "import psycopg2; psycopg2.connect(host='postgres', user='postgres', password='postgres123', dbname='auto_correction')" 2>/dev/null; then
      echo "✅ PostgreSQL local conectado!"
      break
    fi
    echo "Tentativa $i/30... Aguardando PostgreSQL local"
    sleep 2
  done
fi

echo "📊 Executando migrações..."
python migrate.py || echo "⚠️ Migrações já executadas"

echo "🎯 Inicializando dados de exemplo..."
python init_simple.py || echo "⚠️ Dados já inicializados"

echo "🌟 Iniciando Flask API..."
exec python app.py 