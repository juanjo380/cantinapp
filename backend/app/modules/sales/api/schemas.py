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
    location_id: UUID | None = None  # sede; si el usuario tiene una asignada, se usa esa


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
    location_id: UUID | None = None
    location_name: str | None = None


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
    duplicate_rows: int = 0  # total_rows = imported_rows + error_rows + duplicate_rows
    status: str
    errors: list[ImportErrorOut] = []
