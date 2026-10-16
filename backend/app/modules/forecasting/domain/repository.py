"""Puerto del repositorio de predicciones."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.forecasting.domain.entities import Forecast


class ForecastRepository(Protocol):
    async def add(
        self,
        *,
        business_id: UUID,
        product_id: UUID,
        model_type: str,
        history_days: int,
        forecast_days: int,
        forecast_start,
        predicted_demand,
        confidence: float,
        daily_prediction: list[dict],
        created_by: UUID | None,
    ) -> Forecast: ...

    async def latest(self, business_id: UUID, product_id: UUID) -> Forecast | None: ...

    async def list(self, business_id: UUID, product_id: UUID, *, limit: int = 20) -> list[Forecast]: ...
