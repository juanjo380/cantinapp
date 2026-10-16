"""Entidades del dominio de alertas."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class AlertStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"


@dataclass
class Alert:
    id: UUID
    product_id: UUID
    recommendation_id: UUID | None
    current_stock: int
    min_stock: int
    estimated_demand: Decimal | None
    recommended_quantity: int | None
    status: str
    reviewed_at: datetime | None
    created_at: datetime | None
