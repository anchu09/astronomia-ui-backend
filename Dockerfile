FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn>=0.32.0" \
    "httpx>=0.27.0" \
    "pydantic>=2.9.0" \
    "python-dotenv>=1.0.0" \
    "openai>=1.60.0"

COPY app/ ./app/

EXPOSE 3000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
