"""Puerto del repositorio de recomendaciones."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.recommendations.domain.entities import Recommendation
from app.modules.recommendations.domain.policy import RecommendationDraft


class RecommendationRepository(Protocol):
    async def add(
        self, *, business_id: UUID, product_id: UUID, forecast_id: UUID | None, draft: RecommendationDraft
    ) -> Recommendation: ...

    async def latest(self, business_id: UUID, product_id: UUID) -> Recommendation | None: ...

    async def list(self, business_id: UUID, product_id: UUID, *, limit: int = 20) -> list[Recommendation]: ...
