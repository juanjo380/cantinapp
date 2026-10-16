"""Modelos predictivos (puros, sin dependencias). Regresión lineal y promedio
móvil sobre la serie diaria de unidades vendidas (doc 1: modelo predictivo base).

shortcut: modelos base del MVP; no se usa numpy/statsmodels. Si se necesitan
modelos avanzados (ARIMA, Prophet), mover este cálculo a un servicio dedicado.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

_MOVING_AVERAGE_WINDOW = 7


@dataclass
class ForecastResult:
    daily: list[dict]
    total: float
    confidence: float


def dense_series(history: dict[date, int], start: date, end: date) -> list[float]:
    """Serie diaria sin huecos (0 los días sin ventas)."""
    values: list[float] = []
    day = start
    while day <= end:
        values.append(float(history.get(day, 0)))
        day += timedelta(days=1)
    return values


def moving_average(daily: list[float], window: int = _MOVING_AVERAGE_WINDOW) -> float:
    if not daily:
        return 0.0
    recent = daily[-window:] if window > 0 else daily
    return sum(recent) / len(recent)


def linear_regression(daily: list[float]) -> tuple[float, float]:
    """Devuelve (pendiente, intercepto) por mínimos cuadrados."""
    n = len(daily)
    if n == 0:
        return 0.0, 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(daily) / n
    denominator = sum((i - mean_x) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0, mean_y
    slope = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(daily)) / denominator
    return slope, mean_y - slope * mean_x


def _confidence_from_variation(daily: list[float]) -> float:
    mean = sum(daily) / len(daily)
    if mean <= 0:
        return 1.0 if all(v == 0 for v in daily) else 0.5
    variance = sum((v - mean) ** 2 for v in daily) / len(daily)
    cv = math.sqrt(variance) / mean
    return max(0.0, min(1.0, 1.0 - cv))


def _r_squared(daily: list[float], slope: float, intercept: float) -> float:
    mean = sum(daily) / len(daily)
    ss_tot = sum((y - mean) ** 2 for y in daily)
    if ss_tot == 0:
        return 1.0
    ss_res = sum((y - (intercept + slope * i)) ** 2 for i, y in enumerate(daily))
    return max(0.0, min(1.0, 1.0 - ss_res / ss_tot))


def forecast(daily: list[float], forecast_days: int, model: str, start: date) -> ForecastResult:
    """Proyecta `forecast_days` días a partir de `start` (normalmente mañana)."""
    if not daily:
        return ForecastResult(daily=[], total=0.0, confidence=0.0)

    points: list[dict] = []
    if model == "LINEAR_REGRESSION":
        slope, intercept = linear_regression(daily)
        n = len(daily)
        for k in range(1, forecast_days + 1):
            value = max(0.0, intercept + slope * (n - 1 + k))
            points.append({"date": (start + timedelta(days=k - 1)).isoformat(), "value": round(value, 2)})
        confidence = _r_squared(daily, slope, intercept)
    else:
        value = max(0.0, moving_average(daily))
        for k in range(forecast_days):
            points.append({"date": (start + timedelta(days=k)).isoformat(), "value": round(value, 2)})
        confidence = _confidence_from_variation(daily)

    total = round(sum(p["value"] for p in points), 2)
    return ForecastResult(daily=points, total=total, confidence=round(confidence, 4))
