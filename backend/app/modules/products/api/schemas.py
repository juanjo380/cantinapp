"""Esquemas HTTP del módulo de productos (7 campos de HU02)."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=120)
    price: Decimal = Field(ge=0)
    quantity: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=120)
    price: Decimal | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)


class ProductOut(BaseModel):
    id: UUID
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    stock_quantity: int
    min_stock: int
    lead_time_days: int
    is_active: bool


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    limit: int
    offset: int
