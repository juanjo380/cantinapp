"""Entidades del dominio de inventario."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class StockStatus(str, Enum):
    NORMAL = "NORMAL"
    BAJO = "BAJO"
    AGOTADO = "AGOTADO"


class MovementType(str, Enum):
    INITIAL = "INITIAL"
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    ADJUSTMENT = "ADJUSTMENT"


@dataclass
class InventoryItem:
    product_id: UUID
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    stock_quantity: int
    min_stock: int
    lead_time_days: int
    status: str


@dataclass
class InventoryMovement:
    id: int
    product_id: UUID
    movement_type: str
    quantity_change: int
    stock_after: int
    notes: str | None
    created_at: datetime
