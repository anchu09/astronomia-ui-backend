"""BFF: entrada HTTP y enrutado al gateway configurado."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(override=False)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.gateways import DirectGalaxyGateway, N8nGateway
from app.gateways.base import AnalysisGateway
from app.schemas import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger(__name__)


def _create_gateway() -> AnalysisGateway:
    settings = get_settings()
    if settings.orchestrator_mode == "n8n":
        return N8nGateway(webhook_url=settings.n8n_webhook_url)
    return DirectGalaxyGateway(
        base_url=settings.galaxy_api_url,
        api_key=settings.galaxy_api_key,
    )


_gateway: AnalysisGateway | None = None


def get_gateway() -> AnalysisGateway:
    global _gateway
    if _gateway is None:
        _gateway = _create_gateway()
    return _gateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "bff_started",
        extra={"orchestrator_mode": settings.orchestrator_mode, "event": "startup"},
    )
    yield
    # shutdown si hiciera falta
    global _gateway
    _gateway = None


app = FastAPI(
    title="astronomIA UI BFF",
    version="0.1.0",
    description="Backend For Frontend: conecta la UI con astronomIA o con n8n.",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Recibe la petición del frontend y la reenvía al gateway (astronomIA o n8n)."""
    try:
        gateway = get_gateway()
        return await gateway.analyze(request)
    except Exception as e:
        logger.exception("analyze_failed", extra={"request_id": request.request_id})
        raise HTTPException(
            status_code=502,
            detail={
                "request_id": request.request_id,
                "status": "error",
                "summary": f"Error del backend: {str(e)}",
            },
        ) from e
