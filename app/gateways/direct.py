"""Gateway directo al backend de análisis astronomIA.

Usado cuando ORCHESTRATOR_MODE=direct. Cuando tengas n8n, cambia a ORCHESTRATOR_MODE=n8n
y el BFF usará N8nGateway sin tocar el frontend.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.schemas import AnalyzeRequest, AnalyzeResponse


class DirectGalaxyGateway:
    """Llama directamente a POST /analyze del backend astronomIA."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _body(self, request: AnalyzeRequest) -> dict:
        body = request.model_dump(exclude_none=True)
        if request.messages and not request.message:
            body.setdefault("message", request.messages[-1].content if request.messages else "")
        if request.message and not request.messages:
            body.setdefault("messages", [{"role": "user", "content": request.message}])
        return body

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        url = f"{self.base_url}/analyze"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=self._body(request), headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return AnalyzeResponse(
            request_id=data.get("request_id", request.request_id),
            status=data.get("status", "error"),
            summary=data.get("summary", ""),
            results=data.get("results", {}),
            artifacts=data.get("artifacts", []),
            warnings=data.get("warnings", []),
        )

    async def analyze_stream(self, request: AnalyzeRequest) -> AsyncIterator[bytes]:
        """Stream SSE from Galaxy API /analyze/stream."""
        url = f"{self.base_url}/analyze/stream"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=self._body(request), headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk
