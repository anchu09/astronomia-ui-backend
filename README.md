# astronomIA UI — Backend For Frontend (BFF)

Backend que conecta el frontend **astronomIA-ui-front** con la API de análisis de galaxias (**astronomIA-galaxy-api**) o, en el futuro, con el orquestador **n8n**. Modular y fácil de desacoplar.

## Modos de funcionamiento

| Modo | Variable | Comportamiento |
|------|----------|----------------|
| **Directo** (actual) | `ORCHESTRATOR_MODE=direct` | El BFF llama directamente a **astronomIA-galaxy-api** (`POST /analyze`). |
| **n8n** (futuro) | `ORCHESTRATOR_MODE=n8n` | El BFF llama al webhook de n8n; n8n enruta a astronomIA-galaxy-api u otros agentes. |

Solo cambias variables de entorno; el frontend no se toca.

## Estructura

```
app/
├── main.py           # FastAPI, CORS, POST /analyze, GET /health
├── config.py         # Settings (ORCHESTRATOR_MODE, URLs, API key)
├── schemas.py        # Contrato BFF (AnalyzeRequest, AnalyzeResponse)
└── gateways/
    ├── base.py       # AnalysisGateway (abstracto)
    ├── direct.py     # DirectGalaxyGateway → astronomIA
    └── n8n.py        # N8nGateway → n8n (orquestador)
```

El **gateway** es la única pieza que cambia: misma interfaz `analyze(request) -> response`, implementaciones distintas.

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

## Configuración

Crea `.env` en la raíz (o copia de un ejemplo):

```env
# Modo: direct = llamar a astronomIA | n8n = llamar a n8n
ORCHESTRATOR_MODE=direct

# API de galaxias astronomIA-galaxy-api (solo si ORCHESTRATOR_MODE=direct)
GALAXY_API_URL=http://localhost:8000
GALAXY_API_KEY=change-me
# Si astronomIA tiene REQUIRE_API_KEY=false, deja GALAXY_API_KEY vacío.

# n8n (solo si ORCHESTRATOR_MODE=n8n)
# N8N_WEBHOOK_URL=https://tu-n8n.com/webhook/...

# CORS: orígenes permitidos (el frontend en dev suele ser 5173)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Levantar en local

1. **astronomIA-galaxy-api** (en su repo):
   ```bash
   cd astronomIA-galaxy-api && make run
   ```
   Debe quedar en `http://localhost:8000`.

2. **BFF** (este repo):
   ```bash
   cd astronomIA-ui-backend
   uv sync
   uv run uvicorn app.main:app --reload --port 3000
   ```
   O con pip: `pip install -e .` y `uvicorn app.main:app --reload --port 3000`.

   BFF en `http://localhost:3000`.

3. **Frontend** (astronomIA-ui-front):
   En su `.env`:
   ```env
   VITE_API_URL=http://localhost:3000
   ```
   Así el frontend llama al BFF y el BFF a astronomIA-galaxy-api.

## Levantar con Docker

No necesitas Python ni `uv`. Solo Docker.

```bash
cd astronomia-ui-backend
docker compose up --build
```

BFF en **http://localhost:3000**. La Galaxy API debe estar ya levantada en el puerto 8000 (en tu PC o en otro contenedor). El frontend usa `VITE_API_URL=http://localhost:3000`.

Opcional: si la Galaxy API exige API key, crea `.env` con `GALAXY_API_KEY=tu-clave` y en `docker-compose.yml` añade `env_file: .env` al servicio `bff`.

## Cambiar a n8n más adelante

1. Monta n8n y crea el workflow que reciba la petición y enrute a astronomIA (o a otro agente).
2. En el BFF, en `.env`:
   ```env
   ORCHESTRATOR_MODE=n8n
   N8N_WEBHOOK_URL=https://tu-n8n.com/webhook/...
   ```
3. Reinicia el BFF. El frontend sigue usando la misma URL del BFF; no hay que desacoplar nada en la UI.

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /analyze` → mismo contrato que el frontend ya usa (request_id, message, messages, etc.). Respuesta: request_id, status, summary, results, artifacts, warnings.
- `GET /artifacts/{request_id}/image` → proxy a la imagen del Galaxy API (solo en modo `direct`). El frontend usa esta URL para mostrar la imagen de la galaxia en el chat.
