"""Modelos ORM del módulo de productos."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class CategoryRecord(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SupplierRecord(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ProductRecord(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(default=0)
    min_stock: Mapped[int] = mapped_column(default=0)
    lead_time_days: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
