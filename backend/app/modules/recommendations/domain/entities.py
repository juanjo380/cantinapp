"""Entidades del dominio de recomendación."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class Urgency(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


@dataclass
class Recommendation:
    id: UUID
    product_id: UUID
    forecast_id: UUID | None
    current_stock: int
    min_stock: int
    lead_time_days: int
    predicted_demand: Decimal
    coverage_days: float | None
    suggested_quantity: int
    urgency: str
    justification: str
    created_at: datetime | None = None


@dataclass
class CoOccurrence:
    related_product_id: UUID
    related_product_name: str
    peaks: int
    hits: int
    score: float
    computed_at: datetime | None = None
