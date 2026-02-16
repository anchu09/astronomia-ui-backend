"""Gateway to Galaxy API (ORCHESTRATOR_MODE=direct)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.schemas import AnalyzeRequest, AnalyzeResponse


class DirectGalaxyGateway:
    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _body(self, request: AnalyzeRequest) -> dict:
        body = request.model_dump(exclude_none=True)
        if request.messages and not request.message:
            last_user = next(
                (m.content for m in reversed(request.messages) if m.role == "user"),
                None,
            )
            body.setdefault("message", last_user or "")
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
        url = f"{self.base_url}/analyze/stream"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                url,
                json=self._body(request),
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk
