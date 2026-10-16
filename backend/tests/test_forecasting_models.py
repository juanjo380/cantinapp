from datetime import date

from app.modules.forecasting.domain.models import (
    dense_series,
    forecast,
    linear_regression,
    moving_average,
)


def test_dense_series_fills_missing_days():
    history = {date(2026, 1, 1): 2, date(2026, 1, 3): 4}
    values = dense_series(history, date(2026, 1, 1), date(2026, 1, 3))
    assert values == [2.0, 0.0, 4.0]


def test_moving_average_uses_last_window():
    assert moving_average([1, 2, 3, 4, 5, 6, 7, 8], window=7) == 5.0


def test_linear_regression_detects_upward_trend():
    slope, intercept = linear_regression([1, 2, 3, 4, 5])
    assert round(slope, 5) == 1.0
    assert round(intercept, 5) == 1.0


def test_forecast_linear_total_matches_daily_sum():
    daily = [float(i) for i in range(1, 31)]
    result = forecast(daily, forecast_days=3, model="LINEAR_REGRESSION", start=date(2026, 2, 1))
    assert len(result.daily) == 3
    assert result.total == round(sum(p["value"] for p in result.daily), 2)
    assert 0.0 <= result.confidence <= 1.0


def test_forecast_never_negative_on_downtrend():
    daily = [float(10 - i) for i in range(10)]
    result = forecast(daily, forecast_days=30, model="LINEAR_REGRESSION", start=date(2026, 2, 1))
    assert all(point["value"] >= 0 for point in result.daily)
