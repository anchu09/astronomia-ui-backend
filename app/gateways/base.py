"""Gateway: direct Galaxy API or n8n webhook."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas import AnalyzeRequest, AnalyzeResponse


class AnalysisGateway(ABC):
    @abstractmethod
    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        ...

    @abstractmethod
    async def analyze_stream(self, request: AnalyzeRequest) -> AsyncIterator[bytes]:
        ...
