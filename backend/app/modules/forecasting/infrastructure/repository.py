"""Adaptador SQLAlchemy del repositorio de predicciones."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.forecasting.domain.entities import Forecast
from app.modules.forecasting.domain.repository import ForecastRepository
from app.modules.forecasting.infrastructure.models import ForecastRecord


def _to_forecast(record: ForecastRecord) -> Forecast:
    return Forecast(
        id=record.id,
        business_id=record.business_id,
        product_id=record.product_id,
        model_type=record.model_type,
        history_days=record.history_days,
        forecast_days=record.forecast_days,
        forecast_start=record.forecast_start,
        predicted_demand=record.predicted_demand,
        confidence=float(record.confidence) if record.confidence is not None else None,
        daily_prediction=record.daily_prediction or [],
        created_at=record.created_at,
    )


class SqlForecastRepository(ForecastRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, *, business_id, product_id, model_type, history_days, forecast_days, forecast_start, predicted_demand, confidence, daily_prediction, created_by) -> Forecast:
        record = ForecastRecord(
            business_id=business_id,
            product_id=product_id,
            model_type=model_type,
            history_days=history_days,
            forecast_days=forecast_days,
            forecast_start=forecast_start,
            predicted_demand=predicted_demand,
            confidence=confidence,
            daily_prediction=daily_prediction,
            created_by=created_by,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return _to_forecast(record)

    async def latest(self, business_id: UUID, product_id: UUID) -> Forecast | None:
        record = (
            await self.session.execute(
                select(ForecastRecord)
                .where(ForecastRecord.business_id == business_id, ForecastRecord.product_id == product_id)
                .order_by(ForecastRecord.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return _to_forecast(record) if record else None

    async def list(self, business_id: UUID, product_id: UUID, *, limit: int = 20) -> list[Forecast]:
        records = (
            await self.session.execute(
                select(ForecastRecord)
                .where(ForecastRecord.business_id == business_id, ForecastRecord.product_id == product_id)
                .order_by(ForecastRecord.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [_to_forecast(record) for record in records]
