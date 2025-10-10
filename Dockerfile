FROM python:3.11-slim

# Variables de entorno para evitar cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Copiar y dar permisos al script de inicio
COPY start.sh .
RUN chmod +x start.sh

# Exponer puerto
EXPOSE 8000

# Uvicorn directo (migraciones se ejecutan con release_command en fly.toml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]