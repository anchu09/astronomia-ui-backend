"""Gateway hacia el orquestador n8n.

Usado cuando ORCHESTRATOR_MODE=n8n. n8n recibe la petición, enruta a astronomIA
u otro agente, y devuelve una respuesta que adaptamos al contrato del BFF.
"""

from __future__ import annotations

import httpx
from app.schemas import AnalyzeRequest, AnalyzeResponse


class N8nGateway:
    """Llama al webhook de n8n. n8n orquesta y puede llamar a astronomIA u otros backends."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url.rstrip("/")

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        if not self.webhook_url:
            return AnalyzeResponse(
                request_id=request.request_id,
                status="error",
                summary="N8N_WEBHOOK_URL no configurado. Define ORCHESTRATOR_MODE=n8n y N8N_WEBHOOK_URL en .env.",
                results={},
                artifacts=[],
                warnings=[],
            )

        body = request.model_dump(exclude_none=True)

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self.webhook_url, json=body)
            resp.raise_for_status()
            data = resp.json()

        # Adaptar la respuesta de n8n al contrato del BFF (mismo shape que astronomIA)
        return AnalyzeResponse(
            request_id=data.get("request_id", request.request_id),
            status=data.get("status", "success"),
            summary=data.get("summary", ""),
            results=data.get("results", {}),
            artifacts=data.get("artifacts", []),
            warnings=data.get("warnings", []),
        )
