"""Modelo ORM de recomendaciones."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class RecommendationRecord(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    forecast_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    current_stock: Mapped[int]
    min_stock: Mapped[int]
    lead_time_days: Mapped[int]
    predicted_demand: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    coverage_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    suggested_quantity: Mapped[int]
    urgency: Mapped[str]
    justification: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
