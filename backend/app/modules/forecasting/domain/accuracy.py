"""Qué tan acertadas fueron las predicciones pasadas (lógica pura).

Solo cuentan predicciones cuyo periodo ya terminó (el último día predicho es anterior a hoy).
Se compara cada `daily_prediction` con las ventas reales de esos mismos días (0 si no hubo).
Si el mismo periodo se predijo varias veces (el usuario recalculó), cuenta solo la más reciente.
precisión = 1 − WAPE, acotada a 0..1 (None si en el periodo no hubo ventas reales).
"""
from dataclasses import dataclass
from datetime import date, timedelta

from app.modules.forecasting.domain.models import error_metrics


@dataclass
class ForecastAccuracy:
    forecast_id: object
    model_type: str
    forecast_start: date
    forecast_end: date
    predicted_total: float
    actual_total: float
    wape: float | None
    mae: float
    accuracy: float | None


@dataclass
class AccuracySummary:
    items: list[ForecastAccuracy]
    predicted_total: float
    actual_total: float
    wape: float | None
    mae: float | None
    accuracy: float | None


def forecast_end(forecast) -> date:
    return forecast.forecast_start + timedelta(days=forecast.forecast_days - 1)


def _accuracy(wape: float | None) -> float | None:
    return None if wape is None else round(max(0.0, min(1.0, 1.0 - wape)), 4)


def evaluate(forecasts: list, actual: dict[date, int], today: date, limit: int = 20) -> AccuracySummary:
    """`forecasts` ordenadas de la más reciente a la más antigua; `actual` = unidades por día."""
    seen: set[tuple[date, int]] = set()
    items: list[ForecastAccuracy] = []
    all_predicted: list[float] = []
    all_actual: list[float] = []
    for forecast in forecasts:
        period = (forecast.forecast_start, forecast.forecast_days)
        if forecast_end(forecast) >= today or period in seen or not forecast.daily_prediction:
            continue
        seen.add(period)
        predicted = [float(p["value"]) for p in forecast.daily_prediction]
        real = [float(actual.get(date.fromisoformat(p["date"]), 0)) for p in forecast.daily_prediction]
        wape, mae = error_metrics(predicted, real)
        items.append(
            ForecastAccuracy(
                forecast_id=forecast.id,
                model_type=forecast.model_type,
                forecast_start=forecast.forecast_start,
                forecast_end=forecast_end(forecast),
                predicted_total=round(sum(predicted), 2),
                actual_total=round(sum(real), 2),
                wape=round(wape, 4) if wape is not None else None,
                mae=round(mae, 4),
                accuracy=_accuracy(wape),
            )
        )
        all_predicted += predicted
        all_actual += real
        if len(items) == limit:
            break

    if not items:
        return AccuracySummary(items=[], predicted_total=0.0, actual_total=0.0, wape=None, mae=None, accuracy=None)
    wape, mae = error_metrics(all_predicted, all_actual)
    return AccuracySummary(
        items=items,
        predicted_total=round(sum(all_predicted), 2),
        actual_total=round(sum(all_actual), 2),
        wape=round(wape, 4) if wape is not None else None,
        mae=round(mae, 4),
        accuracy=_accuracy(wape),
    )
