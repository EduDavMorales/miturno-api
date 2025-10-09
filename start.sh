#!/bin/bash
set -e

echo "🔄 Ejecutando migraciones de Alembic..."
alembic upgrade head

echo "🚀 Iniciando servidor..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}