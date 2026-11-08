"""Precisión de predicciones pasadas contra ventas reales."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.modules.forecasting.domain.accuracy import evaluate

TODAY = date(2026, 11, 8)


def _forecast(start: date, values: list[float], created: int = 0):
    return SimpleNamespace(
        id=uuid4(),
        model_type="MOVING_AVERAGE",
        forecast_start=start,
        forecast_days=len(values),
        created_at=datetime(2026, 1, 1) + timedelta(minutes=created),
        daily_prediction=[{"date": (start + timedelta(days=i)).isoformat(), "value": v} for i, v in enumerate(values)],
    )


def test_only_finished_periods_are_compared_and_missing_days_count_as_zero():
    done = _forecast(date(2026, 11, 1), [10, 10, 10])  # termina el 3: cumplido
    running = _forecast(date(2026, 11, 6), [5, 5, 5])  # termina el 8 (hoy): aún no
    actual = {date(2026, 11, 1): 8, date(2026, 11, 2): 12}  # el día 3 no hubo ventas
    summary = evaluate([running, done], actual, TODAY)
    assert [i.forecast_id for i in summary.items] == [done.id]
    item = summary.items[0]
    assert (item.predicted_total, item.actual_total, item.forecast_end) == (30, 20, date(2026, 11, 3))
    assert item.wape == 0.7 and item.accuracy == 0.3  # |2|+|2|+|10| = 14 sobre 20 reales


def test_recalculated_period_counts_once_and_aggregate_pools_errors():
    newest = _forecast(date(2026, 10, 1), [4, 4], created=2)
    older_same_period = _forecast(date(2026, 10, 1), [100, 100], created=1)
    other = _forecast(date(2026, 10, 10), [2, 2])
    actual = {date(2026, 10, 1): 4, date(2026, 10, 2): 4, date(2026, 10, 10): 1, date(2026, 10, 11): 3}
    summary = evaluate([newest, older_same_period, other], actual, TODAY)
    assert len(summary.items) == 2
    assert summary.wape == round(2 / 12, 4)


def test_no_finished_forecasts_and_no_sales_are_explained_with_none():
    assert evaluate([_forecast(TODAY, [1])], {}, TODAY).items == []
    summary = evaluate([_forecast(date(2026, 10, 1), [1, 1])], {}, TODAY)
    assert (summary.wape, summary.accuracy, summary.mae) == (None, None, 1.0)
