"""n8n webhook gateway."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.gateways.base import AnalysisGateway
from app.schemas import AnalyzeRequest, AnalyzeResponse


class N8nGateway(AnalysisGateway):
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

        body = self._body(request)
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

    async def analyze_stream(self, request: AnalyzeRequest) -> AsyncIterator[bytes]:
        if not self.webhook_url:
            yield self._sse_event(
                "error",
                {"type": "error", "message": "N8N_WEBHOOK_URL no configurado."},
            )
            yield self._sse_event(
                "end",
                {
                    "type": "end",
                    "request_id": request.request_id,
                    "status": "error",
                    "summary": "N8N_WEBHOOK_URL no configurado.",
                },
            )
            return

        yield self._sse_event("status", {"type": "status", "message": "Procesando…"})

        try:
            body = self._body(request)
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(self.webhook_url, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            yield self._sse_event(
                "error",
                {"type": "error", "message": f"Error al comunicar con n8n: {exc}"},
            )
            yield self._sse_event(
                "end",
                {
                    "type": "end",
                    "request_id": request.request_id,
                    "status": "error",
                    "summary": "No se pudo completar el análisis por un error de comunicación.",
                },
            )
            return

        request_id = data.get("request_id", request.request_id)
        status = data.get("status", "success")
        summary = data.get("summary", "")

        if summary:
            yield self._sse_event("summary", {"type": "summary", "summary": summary})
        yield self._sse_event("end", {
            "type": "end",
            "request_id": request_id,
            "status": status,
            "summary": summary,
        })
