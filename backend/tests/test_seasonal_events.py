"""Fechas comerciales: calendario, picos de años anteriores y compra extra sugerida."""
import asyncio
import math
from datetime import date, timedelta

from app.modules.recommendations.application.handlers import seasonal_plan
from app.modules.recommendations.domain.events import (
    event_extra_units,
    event_lift,
    order_by,
    past_occurrences,
    upcoming_events,
)
from app.modules.inventory.domain.entities import InventoryItem

VALENTINE_2026 = date(2026, 2, 14)


def _series(start: date, end: date, daily: int, peaks: dict[date, int] | None = None) -> dict[date, int]:
    peaks = peaks or {}
    out, day = {}, start
    while day <= end:
        out[day] = peaks.get(day, daily)
        day += timedelta(days=1)
    return out


def test_calendar_rules_for_colombia():
    events = {key: day for key, _, day in upcoming_events(date(2026, 8, 1), 365)}
    assert events["AMOR_AMISTAD"] == date(2026, 9, 19)  # tercer sábado de septiembre
    assert events["DIA_MADRE"] == date(2027, 5, 9)  # segundo domingo de mayo
    assert events["SAN_VALENTIN"] == date(2027, 2, 14)
    upcoming = [key for key, _, _ in upcoming_events(date(2026, 11, 9), 120)]
    assert upcoming[:3] == ["VELITAS", "NAVIDAD", "FIN_DE_ANO"] and "SAN_VALENTIN" in upcoming


def test_past_occurrences_need_baseline_and_finished_window():
    assert past_occurrences("SAN_VALENTIN", before=date(2026, 11, 9), since=date(2025, 10, 1)) == [VALENTINE_2026]
    # Sin las 4 semanas previas de historial no se puede medir el pico.
    assert past_occurrences("SAN_VALENTIN", before=date(2026, 11, 9), since=date(2026, 2, 1)) == []


def test_postday_peak_after_valentine_is_detected_and_flat_products_are_not():
    start, end = date(2025, 10, 1), date(2026, 11, 8)
    postday = _series(start, end, 1, {VALENTINE_2026 + timedelta(days=1): 8, VALENTINE_2026 + timedelta(days=2): 7})
    lift = event_lift(postday, [VALENTINE_2026])
    assert lift is not None and lift.lift > 2.5 and lift.window_units == 18
    assert event_lift(_series(start, end, 10), [VALENTINE_2026]) is None  # sin pico
    assert event_lift(_series(start, end, 0, {VALENTINE_2026: 1}), [VALENTINE_2026]) is None  # pico de 1 u.: ruido


def test_extra_units_and_order_date():
    lift = event_lift(_series(date(2025, 10, 1), date(2026, 11, 8), 1, {VALENTINE_2026: 11}), [VALENTINE_2026])
    # 5 días de ventana × 1 u./día × (veces − 1)
    assert event_extra_units(lift, current_daily=1.0) == math.ceil((lift.lift - 1) * 5)
    assert event_extra_units(lift, current_daily=0.0) == 15  # sin ventas hoy: lo que se vendió en la ventana
    assert order_by(date(2027, 2, 14), lead_time_days=5) == date(2027, 2, 7)


class _Analytics:
    def __init__(self, rows):
        self.rows = rows

    async def first_sale_date(self, business_id, product_id=None):
        return min(day for _, day, _ in self.rows)

    async def business_daily_series(self, business_id, *, days):
        return self.rows


class _Inventory:
    def __init__(self, items):
        self.items = items

    async def list(self, business_id, **_):
        return self.items, len(self.items)


def test_seasonal_plan_lists_upcoming_valentine_with_postday():
    start, today = date(2025, 10, 1), date(2026, 11, 9)
    peaks = {VALENTINE_2026 + timedelta(days=1): 9, VALENTINE_2026 + timedelta(days=2): 6}
    rows = [("postday", d, u) for d, u in _series(start, today - timedelta(days=1), 1, peaks).items()]
    rows += [("agua", d, u) for d, u in _series(start, today - timedelta(days=1), 10).items()]
    items = [
        InventoryItem("postday", "Postday", None, None, 18000, 3, 2, 5, "OK"),
        InventoryItem("agua", "Agua", None, None, 2500, 30, 10, 3, "OK"),
    ]
    plan = asyncio.run(seasonal_plan(_Analytics(rows), _Inventory(items), "b", today=today))
    assert [e["key"] for e in plan] == ["SAN_VALENTIN"]
    (item,) = plan[0]["items"]
    assert item["name"] == "Postday" and item["extra_units"] > 0 and item["order_by"] == date(2027, 2, 7)
