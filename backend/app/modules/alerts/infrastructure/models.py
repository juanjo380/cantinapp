"""Modelo ORM de alertas."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    current_stock: Mapped[int]
    min_stock: Mapped[int]
    estimated_demand: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    recommended_quantity: Mapped[int | None]
    status: Mapped[str] = mapped_column(default="PENDING")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    reviewed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
