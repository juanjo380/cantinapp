"""Esquemas HTTP del módulo de recomendación."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    product_id: UUID
    forecast_days: int | None = Field(default=None, ge=1, le=365)


class RecommendationOut(BaseModel):
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
    created_at: datetime | None


class RecommendationListOut(BaseModel):
    items: list[RecommendationOut]


class CoOccurrenceOut(BaseModel):
    related_product_id: UUID
    related_product_name: str
    score: float
    hits: int
    peaks: int
    computed_at: datetime | None


class CoOccurrenceListOut(BaseModel):
    product_id: UUID
    items: list[CoOccurrenceOut]


class RecomputeAcceptedOut(BaseModel):
    detail: str
