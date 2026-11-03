"""Entidad de dominio de productos."""
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass
class Product:
    id: UUID
    business_id: UUID
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    stock_quantity: int
    min_stock: int
    lead_time_days: int
    is_active: bool


@dataclass
class ProductImport:
    file_name: str
    total_rows: int
    imported_rows: int
    error_rows: int
    status: str  # COMPLETED | FAILED
    errors: list[dict] = field(default_factory=list)
