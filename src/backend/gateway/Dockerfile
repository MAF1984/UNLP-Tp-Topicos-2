FROM python:3.12-slim

WORKDIR /app

# Instalar utilidades de sistema para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar dependencias
COPY src/backend/gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/backend/gateway /app/src/backend/gateway

ENV PYTHONPATH="/app/src/backend/gateway"
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
