"""Contrato de la API del BFF (lo que espera el frontend)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AnalyzeRequest(BaseModel):
    """Request que envía el frontend al BFF (compatible con lo que astronomIA acepta)."""

    request_id: str
    message: str | None = None
    messages: list[ChatMessage] | None = None
    # Opcionales para modo estructurado (el frontend puede no enviarlos)
    target: dict[str, Any] | None = None
    task: str | None = None
    image_url: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    """Response que devuelve el BFF al frontend (el frontend usa .summary)."""

    request_id: str
    status: str  # "success" | "error"
    summary: str
    results: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[dict[str, str]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
