# astronomIA UI BFF

BFF que conecta **astronomia-ui-frontend** con **astronomia-galaxy-api** o con **n8n**. Solo cambia variables de entorno.

## Modos

| Modo | `ORCHESTRATOR_MODE` | Comportamiento |
|------|---------------------|----------------|
| Directo | `direct` | BFF → Galaxy API (`POST /analyze`, `/analyze/stream`) |
| n8n | `n8n` | BFF → webhook n8n → Galaxy API u otros |

## Estructura

```
app/
├── main.py       # FastAPI, CORS, /analyze, /health, /artifacts
├── config.py     # Settings desde env
├── schemas.py    # AnalyzeRequest, AnalyzeResponse
└── gateways/
    ├── base.py   # AnalysisGateway (ABC)
    ├── direct.py # DirectGalaxyGateway
    └── n8n.py    # N8nGateway
```

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) o pip

## Configuración

`.env` en la raíz:

```env
ORCHESTRATOR_MODE=direct
GALAXY_API_URL=http://localhost:8000
GALAXY_API_KEY=
N8N_WEBHOOK_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Ejecución

**Local**

1. Galaxy API en `:8000` (en su repo: `make run`).
2. BFF:
   ```bash
   uv sync && uv run uvicorn app.main:app --reload --port 3000
   ```
3. Frontend con `VITE_API_URL=http://localhost:3000`.

**Docker**

```bash
docker compose up --build
```

BFF en `http://localhost:3000`. Galaxy API debe estar en `:8000` (host o otro contenedor). Con API key: `.env` con `GALAXY_API_KEY` y en `docker-compose.yml` añadir `env_file: .env` al servicio `bff`.

**Usar n8n**

`ORCHESTRATOR_MODE=n8n` y `N8N_WEBHOOK_URL=<url>`. Reiniciar BFF. El frontend no cambia.

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /analyze` → request_id, message/messages; response: request_id, status, summary, results, artifacts, warnings
- `POST /analyze/stream` → SSE (solo modo `direct`)
- `GET /artifacts/{request_id}/image` → proxy imagen Galaxy API (solo modo `direct`)
