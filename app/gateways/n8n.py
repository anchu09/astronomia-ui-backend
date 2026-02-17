"""n8n webhook gateway."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.schemas import AnalyzeRequest, AnalyzeResponse


def _sse_event(event_name: str, payload: dict) -> bytes:
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n".encode("utf-8")


class N8nGateway:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url.rstrip("/")

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
            yield _sse_event(
                "error",
                {"type": "error", "message": "N8N_WEBHOOK_URL no configurado."},
            )
            yield _sse_event(
                "end",
                {
                    "type": "end",
                    "request_id": request.request_id,
                    "status": "error",
                    "summary": "N8N_WEBHOOK_URL no configurado.",
                },
            )
            return

        yield _sse_event("status", {"type": "status", "message": "Procesando…"})

        try:
            body = self._body(request)
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(self.webhook_url, json=body)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            yield _sse_event(
                "error",
                {"type": "error", "message": f"Error al comunicar con n8n: {exc}"},
            )
            yield _sse_event(
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
        artifacts = data.get("artifacts", [])

        if summary:
            yield _sse_event("summary", {"type": "summary", "summary": summary})
        if artifacts or data.get("image_url"):
            ev = {"type": "artifacts", "request_id": request_id}
            if data.get("image_url"):
                ev["image_url"] = data["image_url"]
            yield _sse_event("artifacts", ev)
        yield _sse_event(
            "end",
            {
                "type": "end",
                "request_id": request_id,
                "status": status,
                "summary": summary,
            },
        )
