"""Esquemas HTTP del módulo de inventario."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InventoryItemOut(BaseModel):
    product_id: UUID
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    stock_quantity: int
    min_stock: int
    lead_time_days: int
    status: str


class InventoryListOut(BaseModel):
    items: list[InventoryItemOut]
    total: int
    limit: int
    offset: int


class MovementCreate(BaseModel):
    product_id: UUID
    movement_type: str = Field(pattern="^(PURCHASE|ADJUSTMENT)$")
    quantity_change: int
    notes: str | None = Field(default=None, max_length=300)


class MovementOut(BaseModel):
    id: int
    product_id: UUID
    movement_type: str
    quantity_change: int
    stock_after: int
    notes: str | None
    created_at: datetime


class MovementListOut(BaseModel):
    items: list[MovementOut]
    total: int
    limit: int
    offset: int
