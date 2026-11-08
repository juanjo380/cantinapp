"""Esquemas HTTP del módulo de predicción."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    product_id: UUID
    forecast_days: int | None = Field(default=None, ge=1, le=365)
    # Sin modelo = AUTO: el backtest de los últimos 14 días elige el de menor error.
    model: str | None = Field(default=None, pattern="^(AUTO|LINEAR_REGRESSION|MOVING_AVERAGE|SEASONAL_WEEKLY)$")


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
    confidence: float | None  # 1 − WAPE del backtest (ver forecasting/domain/models.py)
    daily_prediction: list[ForecastPointOut]
    requested_model: str | None = None  # AUTO o el pedido; model_type es el que se usó
    backtest_wape: float | None = None  # error relativo en los 14 días de prueba (0 = perfecto)
    backtest_mae: float | None = None  # unidades de error promedio por día en esa prueba


class ForecastListOut(BaseModel):
    items: list[ForecastOut]


class ForecastAccuracyOut(BaseModel):
    forecast_id: UUID
    model_type: str
    forecast_start: date
    forecast_end: date
    predicted_total: float
    actual_total: float
    wape: float | None  # None si en el periodo no hubo ventas reales
    mae: float
    accuracy: float | None  # 1 − WAPE (0..1)


class AccuracyOut(BaseModel):
    product_id: UUID
    evaluated: int  # predicciones con periodo cumplido (vacío = aún no hay con qué comparar)
    predicted_total: float
    actual_total: float
    wape: float | None
    mae: float | None
    accuracy: float | None
    items: list[ForecastAccuracyOut]
