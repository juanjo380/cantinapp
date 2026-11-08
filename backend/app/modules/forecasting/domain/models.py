"""Modelos predictivos (puros, sin dependencias) sobre la serie diaria de unidades vendidas.

- MOVING_AVERAGE: promedio de los últimos 7 días, plano.
- LINEAR_REGRESSION: tendencia por mínimos cuadrados.
- SEASONAL_WEEKLY: nivel (promedio de 28 días) × factor del día de la semana. Se eligió en
  lugar de Holt-Winters porque este necesita ≥ 2 temporadas completas y ajustar α, β y γ: con
  30 días de historial se sobreajusta. Los factores se encogen hacia 1 cuando hay pocas semanas.
- AUTO: backtest con los últimos 14 días (holdout) y gana el de menor WAPE (empate: MAE, y
  luego el más simple). No se usa MAPE porque explota con días en 0.

confidence = 1 − WAPE del backtest (acotado a 0..1). Si el periodo de prueba no tuvo ventas el
WAPE no existe y se usa 1 / (1 + MAE). Sin historial suficiente para el backtest: None.

shortcut: modelos clásicos en Python puro; si se necesitan modelos avanzados (ARIMA,
Prophet), mover este cálculo a un servicio dedicado con numpy/statsmodels.
"""
from dataclasses import dataclass
from datetime import date, timedelta

AUTO = "AUTO"
MODELS = ("MOVING_AVERAGE", "SEASONAL_WEEKLY", "LINEAR_REGRESSION")  # del más simple al más complejo
HOLDOUT_DAYS = 14
_MOVING_AVERAGE_WINDOW = 7
_SEASON_WINDOW = 28
_SEASON_SHRINK = 1.0  # peso de "factor = 1" frente a cada semana observada
_MIN_TRAIN_DAYS = 7


@dataclass
class ForecastResult:
    daily: list[dict]
    total: float
    confidence: float | None
    model_type: str
    wape: float | None = None
    mae: float | None = None


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


def weekday_factors(daily: list[float], start: date) -> tuple[float, list[float]]:
    """(nivel, factor por día de la semana 0=lunes) de los últimos 28 días; la serie termina el día antes de `start`."""
    recent = daily[-_SEASON_WINDOW:]
    level = sum(recent) / len(recent) if recent else 0.0
    if level <= 0:
        return 0.0, [1.0] * 7
    sums, counts = [0.0] * 7, [0] * 7
    for i, value in enumerate(recent):
        weekday = (start - timedelta(days=len(recent) - i)).weekday()
        sums[weekday] += value
        counts[weekday] += 1
    factors = []
    for total, count in zip(sums, counts):
        raw = (total / count) / level if count else 1.0
        factors.append((count * raw + _SEASON_SHRINK) / (count + _SEASON_SHRINK))
    return level, factors


def predict(daily: list[float], horizon: int, model: str, start: date) -> list[float]:
    """Valores diarios (≥ 0) de `start` a `start + horizon − 1`; `daily` termina el día anterior a `start`."""
    if not daily:
        return [0.0] * horizon
    if model == "LINEAR_REGRESSION":
        slope, intercept = linear_regression(daily)
        n = len(daily)
        return [max(0.0, intercept + slope * (n - 1 + k)) for k in range(1, horizon + 1)]
    if model == "SEASONAL_WEEKLY":
        level, factors = weekday_factors(daily, start)
        return [max(0.0, level * factors[(start + timedelta(days=k)).weekday()]) for k in range(horizon)]
    return [max(0.0, moving_average(daily))] * horizon


def error_metrics(predicted: list[float], actual: list[float]) -> tuple[float | None, float]:
    """(WAPE, MAE). WAPE = Σ|error| / Σ real; None si no hubo ventas reales (no se puede dividir)."""
    if not actual:
        return None, 0.0
    abs_error = sum(abs(p - a) for p, a in zip(predicted, actual))
    total = sum(actual)
    return (abs_error / total if total > 0 else None), abs_error / len(actual)


def backtest(daily: list[float], model: str, start: date) -> tuple[float | None, float] | None:
    """Entrena sin los últimos 14 días y mide el error en ellos. None si la serie es muy corta."""
    if len(daily) < HOLDOUT_DAYS + _MIN_TRAIN_DAYS:
        return None
    train, test = daily[:-HOLDOUT_DAYS], daily[-HOLDOUT_DAYS:]
    return error_metrics(predict(train, HOLDOUT_DAYS, model, start - timedelta(days=HOLDOUT_DAYS)), test)


def confidence_from(wape: float | None, mae: float) -> float:
    if wape is None:
        return round(1.0 / (1.0 + mae), 4)
    return round(max(0.0, min(1.0, 1.0 - wape)), 4)


def forecast(daily: list[float], forecast_days: int, model: str, start: date) -> ForecastResult:
    """Proyecta `forecast_days` días desde `start` (normalmente mañana). `model` puede ser AUTO."""
    scores = {m: backtest(daily, m, start) for m in (MODELS if model == AUTO else (model,))}
    if model == AUTO:
        ranked = [m for m in MODELS if scores[m] is not None]
        # Si el holdout no tuvo ventas, todos tienen WAPE None: decide el MAE.
        chosen = min(ranked, key=lambda m: (scores[m][0] or 0.0, scores[m][1], MODELS.index(m))) if ranked else MODELS[0]
    else:
        chosen = model

    values = predict(daily, forecast_days, chosen, start)
    points = [
        {"date": (start + timedelta(days=k)).isoformat(), "value": round(v, 2)} for k, v in enumerate(values)
    ]
    score = scores.get(chosen)
    wape, mae = score if score else (None, None)
    return ForecastResult(
        daily=points,
        total=round(sum(p["value"] for p in points), 2),
        confidence=confidence_from(wape, mae) if score else None,
        model_type=chosen,
        wape=round(wape, 4) if wape is not None else None,
        mae=round(mae, 4) if mae is not None else None,
    )
