"""Modelo ORM de predicciones."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Numeric, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class ForecastRecord(Base):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    model_type: Mapped[str]
    history_days: Mapped[int]
    forecast_days: Mapped[int]
    forecast_start: Mapped[date]
    predicted_demand: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    daily_prediction: Mapped[list | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
