"""Esquemas HTTP del módulo de alertas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AlertOut(BaseModel):
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


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int
    limit: int
    offset: int


class GenerateAlertsOut(BaseModel):
    created: int
