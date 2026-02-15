# BFF astronomIA — imagen para ejecutar con Docker
FROM python:3.11-slim

WORKDIR /app

# Dependencias (mismas que pyproject.toml)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn>=0.32.0" \
    "httpx>=0.27.0" \
    "pydantic>=2.9.0" \
    "python-dotenv>=1.0.0"

COPY app/ ./app/

EXPOSE 3000

# Escuchar en 0.0.0.0 para que sea accesible desde el host
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
