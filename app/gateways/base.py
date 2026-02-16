"""Gateway abstraction: BFF delegates to backend (Galaxy API or n8n)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import AnalyzeRequest, AnalyzeResponse


class AnalysisGateway(ABC):
    @abstractmethod
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        ...
