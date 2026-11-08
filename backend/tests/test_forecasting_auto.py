"""Modelo estacional semanal, selección AUTO por backtest y confianza derivada del error."""
from datetime import date, timedelta

from app.modules.forecasting.domain.models import backtest, error_metrics, forecast

START = date(2026, 3, 2)  # lunes: la serie termina el domingo anterior


def _weekly_series(days: int, weekday_units: float = 5, weekend_units: float = 20) -> list[float]:
    first = START - timedelta(days=days)
    return [
        weekend_units if (first + timedelta(days=i)).weekday() >= 5 else weekday_units for i in range(days)
    ]


def test_error_metrics_wape_and_mae_handle_zero_sales():
    assert error_metrics([2, 2], [1, 3]) == (0.5, 1.0)
    assert error_metrics([1, 0], [0, 0]) == (None, 0.5)  # sin ventas reales no hay WAPE


def test_weekly_pattern_seasonal_beats_moving_average_and_auto_picks_it():
    daily = _weekly_series(60)
    seasonal_wape, _ = backtest(daily, "SEASONAL_WEEKLY", START)
    average_wape, _ = backtest(daily, "MOVING_AVERAGE", START)
    assert seasonal_wape < average_wape

    result = forecast(daily, 14, "AUTO", START)
    assert result.model_type == "SEASONAL_WEEKLY"
    saturday = next(p for p in result.daily if date.fromisoformat(p["date"]).weekday() == 5)
    monday = result.daily[0]
    assert saturday["value"] > 2 * monday["value"]
    assert result.confidence > 0.8


def test_flat_series_ties_and_auto_keeps_the_simplest_model():
    result = forecast([5.0] * 45, 7, "AUTO", START)
    assert result.model_type == "MOVING_AVERAGE"
    assert (result.wape, result.mae, result.confidence) == (0.0, 0.0, 1.0)
    assert all(p["value"] == 5.0 for p in result.daily)


def test_series_with_many_zeros_stays_valid():
    daily = [0.0] * 40
    daily[5] = daily[20] = 3.0  # ventas esporádicas y holdout sin ventas
    result = forecast(daily, 10, "AUTO", START)
    assert result.wape is None and result.mae is not None
    assert 0.0 <= result.confidence <= 1.0
    assert all(p["value"] >= 0 for p in result.daily)

    empty = forecast([0.0] * 30, 5, "SEASONAL_WEEKLY", START)
    assert empty.total == 0.0 and empty.confidence == 1.0


def test_short_series_of_30_days_works_with_every_model():
    daily = _weekly_series(30)
    for model in ("AUTO", "MOVING_AVERAGE", "LINEAR_REGRESSION", "SEASONAL_WEEKLY"):
        result = forecast(daily, 30, model, START)
        assert len(result.daily) == 30 and result.confidence is not None


def test_explicit_model_is_respected_and_too_short_series_has_no_confidence():
    assert forecast(_weekly_series(60), 7, "LINEAR_REGRESSION", START).model_type == "LINEAR_REGRESSION"
    assert forecast([1.0] * 10, 3, "AUTO", START).confidence is None
