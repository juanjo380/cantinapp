"""Entidad de dominio de productos."""
from dataclasses import dataclass
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
