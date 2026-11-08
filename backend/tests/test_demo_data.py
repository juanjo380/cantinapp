"""Datos de ejemplo: deterministas, identificables y útiles para predicción, alertas y co-ocurrencia."""
from collections import defaultdict
from datetime import date, timedelta

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.demo.application.service import _require_owner
from app.modules.demo.domain import generator
from app.modules.forecasting.domain.models import dense_series, forecast
from app.modules.recommendations.domain.cooccurrence import cooccurrence_scores

TODAY = date(2026, 11, 8)


def _series():
    first = TODAY - timedelta(days=generator.DAYS - 1)
    history = defaultdict(dict)
    for sale in generator.sales(TODAY):
        history[sale.product][sale.sale_date] = sale.quantity
    return {p: dense_series(days, first, TODAY) for p, days in history.items()}, first


def test_catalog_is_identifiable_and_has_stock_alerts():
    catalog = generator.products()
    assert 10 <= len(catalog) <= 15
    assert all(p.name.endswith(generator.SUFFIX) for p in catalog)
    assert sum(1 for p in catalog if p.stock < p.min_stock) >= 3  # aparecen alertas desde el inicio


def test_sales_are_deterministic_and_cover_90_days():
    rows = generator.sales(TODAY)
    assert rows == generator.sales(TODAY)
    days = {r.sale_date for r in rows}
    assert min(days) == TODAY - timedelta(days=89) and max(days) == TODAY
    assert all(r.quantity > 0 for r in rows)


def test_weekly_pattern_is_picked_by_the_auto_forecast():
    series, _ = _series()
    result = forecast(series[1], 14, "AUTO", TODAY + timedelta(days=1))  # gaseosa
    fridays = [p["value"] for p in result.daily if date.fromisoformat(p["date"]).weekday() == 4]
    sundays = [p["value"] for p in result.daily if date.fromisoformat(p["date"]).weekday() == 6]
    assert min(fridays) > max(sundays)


def test_empanada_peaks_lift_gaseosa_in_cooccurrence():
    series, _ = _series()
    pairs = cooccurrence_scores(series)
    assert any(p.product_id == 0 and p.related_product_id == 1 for p in pairs)


def test_only_the_owner_can_load_or_delete():
    _require_owner("OWNER")
    for role in ("ADMIN", "MEMBER"):
        with pytest.raises(ForbiddenError):
            _require_owner(role)
