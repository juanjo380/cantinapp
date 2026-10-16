"""Adaptador SQLAlchemy del repositorio de recomendaciones."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recommendations.domain.entities import Recommendation
from app.modules.recommendations.domain.policy import RecommendationDraft
from app.modules.recommendations.domain.repository import RecommendationRepository
from app.modules.recommendations.infrastructure.models import RecommendationRecord


def _to_recommendation(record: RecommendationRecord) -> Recommendation:
    return Recommendation(
        id=record.id,
        product_id=record.product_id,
        forecast_id=record.forecast_id,
        current_stock=record.current_stock,
        min_stock=record.min_stock,
        lead_time_days=record.lead_time_days,
        predicted_demand=record.predicted_demand,
        coverage_days=float(record.coverage_days) if record.coverage_days is not None else None,
        suggested_quantity=record.suggested_quantity,
        urgency=record.urgency,
        justification=record.justification,
        created_at=record.created_at,
    )


class SqlRecommendationRepository(RecommendationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self, *, business_id: UUID, product_id: UUID, forecast_id: UUID | None, draft: RecommendationDraft
    ) -> Recommendation:
        record = RecommendationRecord(
            business_id=business_id,
            product_id=product_id,
            forecast_id=forecast_id,
            current_stock=draft.current_stock,
            min_stock=draft.min_stock,
            lead_time_days=draft.lead_time_days,
            predicted_demand=draft.predicted_demand,
            coverage_days=draft.coverage_days,
            suggested_quantity=draft.suggested_quantity,
            urgency=draft.urgency,
            justification=draft.justification,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return _to_recommendation(record)

    async def latest(self, business_id: UUID, product_id: UUID) -> Recommendation | None:
        record = (
            await self.session.execute(
                select(RecommendationRecord)
                .where(
                    RecommendationRecord.business_id == business_id,
                    RecommendationRecord.product_id == product_id,
                )
                .order_by(RecommendationRecord.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_recommendation(record) if record else None

    async def list(self, business_id: UUID, product_id: UUID, *, limit: int = 20) -> list[Recommendation]:
        records = (
            await self.session.execute(
                select(RecommendationRecord)
                .where(
                    RecommendationRecord.business_id == business_id,
                    RecommendationRecord.product_id == product_id,
                )
                .order_by(RecommendationRecord.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [_to_recommendation(record) for record in records]
