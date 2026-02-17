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

Pon `ORCHESTRATOR_MODE=n8n` y `N8N_WEBHOOK_URL=<url del webhook>` en el `.env`, reinicia el BFF. El frontend no cambia.

## n8n como enrutador

El BFF envía las peticiones del chat al webhook de n8n en lugar de a la Galaxy API. n8n puede decidir si reenviar a la Galaxy API o a otro agente según el mensaje.

**.env del BFF:** `ORCHESTRATOR_MODE=n8n`, `N8N_WEBHOOK_URL=https://...`

**En n8n:** Workflow con Webhook (POST, JSON). El body es el mismo que usa la Galaxy API (`request_id`, `message`, `messages`). Enruta por contenido (IF/Switch en `body.message` o un clasificador) y responde con JSON:

```json
{
  "request_id": "...",
  "status": "success",
  "summary": "Texto de respuesta",
  "results": {},
  "artifacts": [],
  "warnings": []
}
```

Si hay imagen y no usas el proxy del BFF (solo en modo direct), incluye `image_url` con la URL pública de la imagen; el frontend la usa.

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /analyze` — body: request_id, message/messages. Respuesta: request_id, status, summary, results, artifacts, warnings.
- `POST /analyze/stream` — mismo body, respuesta SSE (status, summary, artifacts, end). Con n8n el BFF llama al webhook y convierte la respuesta a SSE.
- `GET /artifacts/{request_id}/image` — proxy a Galaxy API (solo modo direct)
