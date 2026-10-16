"""Modelo ORM del libro de movimientos de inventario."""
import uuid
from datetime import datetime

from sqlalchemy import Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class MovementRecord(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    movement_type: Mapped[str]
    quantity_change: Mapped[int]
    stock_after: Mapped[int] = mapped_column(default=0)
    sale_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
