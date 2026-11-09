"""Esquemas HTTP del módulo de recomendación."""
from datetime import date, datetime
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


class PlanItemOut(BaseModel):
    product_id: UUID
    name: str
    category: str | None
    current_stock: int
    min_stock: int
    lead_time_days: int
    daily_demand: float
    coverage_days: float | None
    suggested_quantity: int
    urgency: str
    confidence: float | None
    model_type: str


class PlanOut(BaseModel):
    items: list[PlanItemOut]
    pending: list[str]  # productos sin historial suficiente para predecir


class SeasonalItemOut(BaseModel):
    product_id: UUID
    name: str
    lift: float  # veces lo normal alrededor de la fecha, en años anteriores
    usual_daily: float
    past_window_units: float
    years: int
    extra_units: int
    current_stock: int
    order_by: date


class SeasonalEventOut(BaseModel):
    key: str
    name: str
    date: date
    days_until: int
    items: list[SeasonalItemOut]


class SeasonalOut(BaseModel):
    events: list[SeasonalEventOut]
