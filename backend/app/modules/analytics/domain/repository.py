"""Puerto del repositorio de análisis histórico (RF-10, RF-11)."""
from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from app.modules.analytics.domain.entities import ProductRanking, SalesSeriesPoint


class AnalyticsRepository(Protocol):
    async def sales_series(
        self,
        business_id: UUID,
        *,
        period: str,
        date_from: date,
        date_to: date,
        product_id: UUID | None = None,
    ) -> list[SalesSeriesPoint]: ...

    async def product_ranking(
        self,
        business_id: UUID,
        *,
        order: str,
        limit: int,
        date_from: date,
        date_to: date,
    ) -> list[ProductRanking]: ...

    async def daily_series(
        self, business_id: UUID, product_id: UUID, *, days: int
    ) -> list[tuple[date, int]]: ...

    async def business_daily_series(self, business_id: UUID, *, days: int) -> list[tuple[UUID, date, int]]: ...

    async def first_sale_date(self, business_id: UUID, product_id: UUID | None = None) -> date | None: ...
