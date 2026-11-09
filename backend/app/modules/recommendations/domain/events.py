"""Fechas comerciales (Colombia) y cuánto más vende cada producto alrededor de ellas. Lógica pura.

Idea: lo que se vendió alrededor de la misma fecha en años anteriores, comparado con las 4
semanas previas, dice qué productos se disparan (p. ej. la Postday después de San Valentín,
que nadie tiene en cuenta). La ventana va de 2 días antes a 2 días después: hay productos que
suben antes (chocolates) y otros después (Postday, Alka-Seltzer el 1 de enero).
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

WINDOW_BEFORE = 2
WINDOW_AFTER = 2
WINDOW_DAYS = WINDOW_BEFORE + 1 + WINDOW_AFTER
BASELINE_DAYS = 28
MIN_LIFT = 1.5  # menos que esto es ruido normal de la semana
MIN_WINDOW_UNITS = 3  # un pico de 1 o 2 unidades no justifica una compra
_SMOOTHING = 0.5  # u./día sumadas arriba y abajo: un producto con base 0 no da un "pico infinito"


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


# (clave, nombre, fecha según el año)
EVENTS = (
    ("SAN_VALENTIN", "San Valentín", lambda y: date(y, 2, 14)),
    ("DIA_MUJER", "Día de la Mujer", lambda y: date(y, 3, 8)),
    ("DIA_MADRE", "Día de la Madre", lambda y: _nth_weekday(y, 5, 6, 2)),
    ("DIA_PADRE", "Día del Padre", lambda y: _nth_weekday(y, 6, 6, 3)),
    ("AMOR_AMISTAD", "Amor y Amistad", lambda y: _nth_weekday(y, 9, 5, 3)),
    ("HALLOWEEN", "Halloween", lambda y: date(y, 10, 31)),
    ("VELITAS", "Día de las Velitas", lambda y: date(y, 12, 7)),
    ("NAVIDAD", "Navidad", lambda y: date(y, 12, 24)),
    ("FIN_DE_ANO", "Fin de año", lambda y: date(y, 12, 31)),
)


def upcoming_events(today: date, horizon_days: int) -> list[tuple[str, str, date]]:
    """Fechas cuya ventana aún no termina y empiezan dentro del horizonte, en orden."""
    found = []
    for key, name, rule in EVENTS:
        for year in (today.year, today.year + 1):
            day = rule(year)
            if day + timedelta(days=WINDOW_AFTER) >= today and (day - today).days <= horizon_days:
                found.append((key, name, day))
                break
    return sorted(found, key=lambda event: event[2])


def past_occurrences(key: str, before: date, since: date) -> list[date]:
    """Fechas del mismo evento en años anteriores con historial suficiente (ventana + línea base)."""
    rule = next(rule for k, _, rule in EVENTS if k == key)
    days = []
    for year in range(since.year, before.year + 1):
        day = rule(year)
        if day - timedelta(days=WINDOW_BEFORE + BASELINE_DAYS) >= since and day + timedelta(days=WINDOW_AFTER) < before:
            days.append(day)
    return days


@dataclass
class EventLift:
    lift: float  # cuántas veces lo normal se vende en la ventana
    baseline_daily: float  # u./día en las 4 semanas previas (la más reciente)
    window_units: float  # u. vendidas en la ventana (promedio de los años vistos)
    years: int


def event_lift(daily: dict[date, int], occurrences: list[date]) -> EventLift | None:
    """Pico promedio del producto en las ocurrencias pasadas; None si no hay pico relevante."""
    lifts, windows, baselines = [], [], []
    for day in occurrences:
        start = day - timedelta(days=WINDOW_BEFORE)
        window = sum(daily.get(start + timedelta(days=i), 0) for i in range(WINDOW_DAYS))
        baseline = sum(daily.get(start - timedelta(days=i), 0) for i in range(1, BASELINE_DAYS + 1)) / BASELINE_DAYS
        lifts.append((window / WINDOW_DAYS + _SMOOTHING) / (baseline + _SMOOTHING))
        windows.append(window)
        baselines.append(baseline)
    if not lifts:
        return None
    lift = sum(lifts) / len(lifts)
    window_units = sum(windows) / len(windows)
    if lift < MIN_LIFT or window_units < MIN_WINDOW_UNITS:
        return None
    return EventLift(round(lift, 2), round(baselines[-1], 2), round(window_units, 1), len(lifts))


def event_extra_units(lift: EventLift, current_daily: float) -> int:
    """Unidades a comprar de más para la fecha, encima de la reposición normal (que ya cubre la
    lista de compra). El pico se escala a la venta de hoy: si el negocio creció, el pico también."""
    if current_daily <= 0:
        return math.ceil(lift.window_units)
    return max(0, math.ceil(current_daily * (lift.lift - 1) * WINDOW_DAYS))


def order_by(event_day: date, lead_time_days: int) -> date:
    """Último día para pedir y tenerlo antes de que empiece la ventana."""
    return event_day - timedelta(days=WINDOW_BEFORE + lead_time_days)
