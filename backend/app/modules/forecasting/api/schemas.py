"""Esquemas HTTP del módulo de predicción."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    product_id: UUID
    forecast_days: int | None = Field(default=None, ge=1, le=365)
    model: str | None = Field(default=None, pattern="^(LINEAR_REGRESSION|MOVING_AVERAGE)$")


class ForecastPointOut(BaseModel):
    date: str
    value: float


class ForecastOut(BaseModel):
    id: UUID
    product_id: UUID
    model_type: str
    history_days: int
    forecast_days: int
    forecast_start: date
    predicted_demand: Decimal
    confidence: float | None
    daily_prediction: list[ForecastPointOut]


class ForecastListOut(BaseModel):
    items: list[ForecastOut]
