"""Entidades del dominio de ventas."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass
class Sale:
    id: UUID
    business_id: UUID
    product_id: UUID
    sale_date: date
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    source: str
    affects_inventory: bool


@dataclass
class SaleImport:
    id: UUID
    file_name: str
    total_rows: int
    imported_rows: int
    error_rows: int
    status: str
    errors: list[dict] = field(default_factory=list)
    affects_inventory: bool = False
