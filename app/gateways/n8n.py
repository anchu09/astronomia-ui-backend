"""Gateway to n8n webhook (ORCHESTRATOR_MODE=n8n)."""

from __future__ import annotations

import httpx

from app.schemas import AnalyzeRequest, AnalyzeResponse


class N8nGateway:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url.rstrip("/")

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        if not self.webhook_url:
            return AnalyzeResponse(
                request_id=request.request_id,
                status="error",
                summary="N8N_WEBHOOK_URL no configurado.",
                results={},
                artifacts=[],
                warnings=[],
            )

        body = request.model_dump(exclude_none=True)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self.webhook_url, json=body)
            resp.raise_for_status()
            data = resp.json()

        return AnalyzeResponse(
            request_id=data.get("request_id", request.request_id),
            status=data.get("status", "success"),
            summary=data.get("summary", ""),
            results=data.get("results", {}),
            artifacts=data.get("artifacts", []),
            warnings=data.get("warnings", []),
        )
