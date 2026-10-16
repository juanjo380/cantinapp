"""Modelos ORM del módulo de ventas. El movimiento de inventario lo genera el
trigger de la BD (RF-08), no el backend."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Computed, Numeric, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class SaleImportRecord(Base):
    __tablename__ = "sales_imports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    file_name: Mapped[str]
    total_rows: Mapped[int] = mapped_column(default=0)
    imported_rows: Mapped[int] = mapped_column(default=0)
    error_rows: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="PROCESSING")
    error_detail: Mapped[list | None] = mapped_column(JSONB)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SaleRecord(Base):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    sale_date: Mapped[date]
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), Computed("quantity * unit_price")
    )
    source: Mapped[str] = mapped_column(default="MANUAL")
    affects_inventory: Mapped[bool] = mapped_column(default=True)
    import_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
