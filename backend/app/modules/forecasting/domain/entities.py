"""Entidades del dominio de predicción."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class ModelType(str, Enum):
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    MOVING_AVERAGE = "MOVING_AVERAGE"


@dataclass
class Forecast:
    id: UUID
    business_id: UUID
    product_id: UUID
    model_type: str
    history_days: int
    forecast_days: int
    forecast_start: date
    predicted_demand: Decimal
    confidence: float
    daily_prediction: list[dict]
    created_at: datetime | None = None
