#!/bin/bash
set -e

echo "🚀 Aguardando PostgreSQL..."

# Esperar PostgreSQL ficar pronto
for i in {1..30}; do
  if python -c "import psycopg2; psycopg2.connect(host='postgres', user='postgres', password='postgres123', dbname='ufpi_ic')" 2>/dev/null; then
    echo "✅ PostgreSQL conectado!"
    break
  fi
  echo "Tentativa $i/30... Aguardando PostgreSQL"
  sleep 2
done

echo "📊 Executando migrações..."
python migrate.py || echo "⚠️ Migrações já executadas"

echo "🎯 Inicializando dados de exemplo..."
python init_simple.py || echo "⚠️ Dados já inicializados"

echo "🌟 Iniciando Flask API..."
exec python app.py 