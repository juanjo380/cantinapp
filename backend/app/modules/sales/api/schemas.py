"""Esquemas HTTP del módulo de ventas."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    product_id: UUID
    sale_date: date
    quantity: int = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


class SaleOut(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str | None = None
    sale_date: date
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    source: str
    affects_inventory: bool


class SaleListOut(BaseModel):
    items: list[SaleOut]
    total: int
    limit: int
    offset: int


class ImportErrorOut(BaseModel):
    row: int
    field: str
    message: str


class ImportOut(BaseModel):
    id: UUID
    file_name: str
    total_rows: int
    imported_rows: int
    error_rows: int
    status: str
    errors: list[ImportErrorOut] = []
