#!/bin/bash
set -e

echo "🔄 Creando tablas base..."
python -c "from app.database import engine; from app.models.user import Base; Base.metadata.create_all(bind=engine)"

echo "🔄 Ejecutando migraciones de Alembic..."
alembic upgrade head

echo "🚀 Iniciando servidor..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}