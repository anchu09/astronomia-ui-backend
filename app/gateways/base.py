"""Contrato del gateway: abstracción para desacoplar BFF del backend real.

Implementaciones:
- DirectGalaxyGateway: llama a astronomIA (modo actual).
- N8nGateway: llama a n8n, que enruta a astronomIA u otros (modo futuro).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import AnalyzeRequest, AnalyzeResponse


class AnalysisGateway(ABC):
    """Gateway de análisis: un único método que el BFF usa para enviar la petición."""

    @abstractmethod
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """Envía la petición al backend (astronomIA o n8n) y devuelve la respuesta normalizada."""
        ...
