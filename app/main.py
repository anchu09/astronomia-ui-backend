"""BFF: frontend → gateway (Galaxy API o n8n)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv

load_dotenv(override=False)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

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
    global _gateway
    _gateway = None


app = FastAPI(
    title="astronomIA UI BFF",
    version="0.1.0",
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


@app.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest) -> StreamingResponse:
    gateway = get_gateway()
    return StreamingResponse(
        gateway.analyze_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/artifacts/{request_id}/image")
async def get_artifact_image(request_id: str):
    settings = get_settings()
    if settings.orchestrator_mode != "direct":
        raise HTTPException(
            status_code=404,
            detail="Artifact proxy only available when ORCHESTRATOR_MODE=direct.",
        )
    url = f"{settings.galaxy_api_url}/artifacts/{request_id}/image"
    headers = {}
    if settings.galaxy_api_key:
        headers["X-API-Key"] = settings.galaxy_api_key
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Image not found for this request.")
    resp.raise_for_status()
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "image/jpeg"),
    )
