# Prueba end-to-end (stack astronomIA)

Flujo típico: **usuario escribe un prompt** → **frontend** → **BFF** → **Galaxy API** y/o **n8n** (según `ORCHESTRATOR_MODE`) → respuesta en el chat.

## Requisitos

- **Galaxy API**: Python 3.11+, `OPENAI_API_KEY` en `.env` (y `API_KEY` si `REQUIRE_API_KEY=true`).
- **BFF**: Python 3.11+ o Docker.
- **Frontend**: Node 18+ o Docker.

## Puertos

| Servicio    | Puerto | URL base               |
|------------|--------|-------------------------|
| Galaxy API | 8000   | http://localhost:8000   |
| BFF        | 3000   | http://localhost:3000   |
| Frontend   | 5173   | http://localhost:5173   |

## 1. Galaxy API

```bash
cd astronomia-galaxy-api
cp .env.example .env
# Editar .env: OPENAI_API_KEY, etc.
make install && make run
```

Comprobar: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## 2. BFF

**Docker** (en la carpeta `astronomia-ui-backend`):

```bash
cp .env.example .env
# Ajustar ORCHESTRATOR_MODE (direct | n8n | auto), OPENAI_API_KEY si auto,
# N8N_WEBHOOK_URL si n8n o auto con planificación.
docker compose up --build
```

El `docker-compose.yml` usa `env_file: .env` y fuerza `GALAXY_API_URL=http://host.docker.internal:8000` para alcanzar la API en el host.

**Local con uv:**

```bash
uv sync && uv run uvicorn app.main:app --reload --port 3000
```

Comprobar: `curl http://localhost:3000/health` → `{"status":"ok"}`.

## 3. Frontend

**Docker:**

```bash
cd astronomia-ui-frontend
docker compose up --build
```

**Local:**

```bash
cp .env.example .env   # VITE_API_URL=http://localhost:3000
npm install && npm run dev
```

Abrir **http://localhost:5173**.

## 4. Prueba en el chat

Iniciar sesión (flujo demo), enviar por ejemplo un análisis de galaxia o, en modo **auto**, una petición con lugar terrestre si debe enrutar a n8n.

## Si algo falla

- **502 / BFF sin Galaxy**: API no está en `:8000` o URL incorrecta en Docker (`host.docker.internal` en Windows/Mac con Docker Desktop).
- **Sin imagen en modo direct**: comprobar `artifacts` y `GET /artifacts/{id}/image`.
- **n8n / auto no enrutan**: revisar `.env` del BFF y que el contenedor se haya recreado tras cambiar variables (`docker compose up --build`).
