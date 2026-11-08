"""Puerto del repositorio de predicciones."""
from __future__ import annotations

from datetime import date
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
        confidence: float | None,
        daily_prediction: list[dict],
        created_by: UUID | None,
        requested_model: str | None = None,
        backtest_wape: float | None = None,
        backtest_mae: float | None = None,
    ) -> Forecast: ...

    async def latest(self, business_id: UUID, product_id: UUID) -> Forecast | None: ...

    async def list(self, business_id: UUID, product_id: UUID, *, limit: int = 20) -> list[Forecast]: ...

    async def finished(self, business_id: UUID, product_id: UUID, *, before: date, limit: int) -> list[Forecast]:
        """Predicciones cuyo último día es anterior a `before`, de la más reciente a la más antigua."""
