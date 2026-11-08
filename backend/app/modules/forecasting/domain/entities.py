"""Entidades del dominio de predicción."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class ModelType(str, Enum):
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    MOVING_AVERAGE = "MOVING_AVERAGE"
    SEASONAL_WEEKLY = "SEASONAL_WEEKLY"
    AUTO = "AUTO"  # solo como modelo pedido: se guarda el que ganó el backtest


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
    confidence: float | None
    daily_prediction: list[dict]
    created_at: datetime | None = None
    requested_model: str | None = None  # AUTO o el modelo que pidió el usuario (NULL antes de 006)
    backtest_wape: float | None = None
    backtest_mae: float | None = None
