"""Configuración desde variables de entorno.

Modo de orquestación:
- ORCHESTRATOR_MODE=direct  → BFF llama directamente al backend astronomIA.
- ORCHESTRATOR_MODE=n8n     → BFF llama a n8n (orquestador); n8n enruta a astronomIA u otros.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

OrchestratorMode = Literal["direct", "n8n"]


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


def _bool(key: str, default: bool = False) -> bool:
    v = _env(key).lower()
    return v in ("1", "true", "yes", "y", "on")


@dataclass(frozen=True)
class Settings:
    """Configuración del BFF."""

    # Modo: direct = llamar a astronomIA; n8n = llamar al orquestador n8n
    orchestrator_mode: OrchestratorMode

    # Backend de análisis de galaxias (solo usado si orchestrator_mode == "direct")
    galaxy_api_url: str
    galaxy_api_key: str  # opcional; si está definida se envía como X-API-Key

    # Orquestador n8n (solo usado si orchestrator_mode == "n8n")
    n8n_webhook_url: str  # URL del webhook que recibe la petición y enruta

    # CORS: permitir origen del frontend
    cors_origins: list[str]

    @classmethod
    def from_env(cls) -> Settings:
        mode = _env("ORCHESTRATOR_MODE", "direct").lower()
        if mode not in ("direct", "n8n"):
            mode = "direct"
        orchestrator_mode: OrchestratorMode = mode  # type: ignore[assignment]

        galaxy_api_url = _env("GALAXY_API_URL", "http://localhost:8000").rstrip("/")
        galaxy_api_key = _env("GALAXY_API_KEY", "")
        n8n_webhook_url = _env("N8N_WEBHOOK_URL", "").rstrip("/")

        origins = _env("CORS_ORIGINS", "http://localhost:5173")
        cors_origins = [o.strip() for o in origins.split(",") if o.strip()] or ["http://localhost:5173"]

        return cls(
            orchestrator_mode=orchestrator_mode,
            galaxy_api_url=galaxy_api_url,
            galaxy_api_key=galaxy_api_key,
            n8n_webhook_url=n8n_webhook_url,
            cors_origins=cors_origins,
        )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
