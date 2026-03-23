# astronomIA UI Backend (BFF)

BFF que conecta **astronomia-ui-frontend** con **astronomia-galaxy-api** (o n8n). Proxy en FastAPI, reenvía peticiones y SSE.

## Modos

| Modo | `ORCHESTRATOR_MODE` | Flujo |
|------|---------------------|-------|
| Directo | `direct` | BFF → Galaxy API (`/analyze/stream`, `/artifacts`) |
| n8n | `n8n` | BFF → webhook n8n → Galaxy API u otros servicios |

## Estructura

```
app/
├── __init__.py
├── main.py       # FastAPI, CORS, rutas /health, /analyze, /analyze/stream, /artifacts
├── config.py     # Settings desde env
├── schemas.py    # AnalyzeRequest (+ ChatMessage), AnalyzeResponse
└── gateways/
    ├── __init__.py
    ├── base.py   # AnalysisGateway (ABC): analyze() + analyze_stream()
    ├── direct.py # DirectGalaxyGateway — proxy a Galaxy API con streaming SSE
    └── n8n.py    # N8nGateway — webhook a n8n, convierte respuesta a SSE
```

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) o pip

## Configuración

Crear `.env` en la raíz (ver `.env.example`):

```env
ORCHESTRATOR_MODE=direct
GALAXY_API_URL=http://localhost:8000
GALAXY_API_KEY=
N8N_WEBHOOK_URL=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Ejecución

**Local:**

1. Galaxy API en `:8000` (en su repo: `make run`).
2. BFF:
   ```bash
   uv sync && uv run uvicorn app.main:app --reload --port 3000
   ```
3. Frontend con `VITE_API_URL=http://localhost:3000`.

**Docker:**

```bash
docker compose up --build
```

BFF en `http://localhost:3000`. Galaxy API debe estar en `:8000` (host o contenedor). Con API key: añadir `GALAXY_API_KEY` en `.env` y `env_file: .env` al servicio en `docker-compose.yml`.

## Modo n8n

Usa n8n como enrutador entre el frontend y otros backends.

1. En `.env`: `ORCHESTRATOR_MODE=n8n` y `N8N_WEBHOOK_URL=<url>`.
2. El BFF envía las peticiones al webhook. n8n decide a qué servicio reenviar según el mensaje.
3. n8n responde con el mismo esquema JSON que la Galaxy API:

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

Si hay imagen y no se usa el proxy del BFF, incluir `image_url` con la URL pública; el frontend la usa directamente.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | `{"status":"ok"}` |
| `POST` | `/analyze` | Análisis síncrono. Body: `request_id`, `message`/`messages`, `target`, `task`, `image_url`, `options`. Respuesta JSON |
| `POST` | `/analyze/stream` | Mismo body, respuesta SSE (`status`, `summary`, `artifacts`, `end`, `error`). En modo n8n el BFF convierte la respuesta JSON a SSE |
| `GET` | `/artifacts/{request_id}/image` | Proxy a la imagen de Galaxy API (solo modo `direct`) |

## Tests y calidad

```bash
make install # uv sync --group dev
make run     # uvicorn con --reload en :3000
make test    # pytest (sin tests por ahora)
make lint    # ruff
```

### Normalización del body

Los gateways normalizan automáticamente los campos `message` y `messages`: si envías solo `messages`, extrae el último mensaje de usuario como `message`; si envías solo `message`, lo envuelve en un array `messages`.

### Autenticación

Las peticiones al Galaxy API incluyen el header `X-API-Key` con el valor de `GALAXY_API_KEY`.

### Timeouts

| Ruta | Timeout |
|------|---------|
| `POST /analyze` | 120s |
| `POST /analyze/stream` | connect 15s, write 30s, read sin límite |
| `GET /artifacts/.../image` | 30s |
