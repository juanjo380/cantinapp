"""Patrón semanal agregado entre negocios (ML_ANONYMOUS) usado como prior del modelo estacional."""
from datetime import date

from app.modules.forecasting.domain.models import MIN_POOL_BUSINESSES, forecast, pooled_prior, weekday_factors

START = date(2026, 3, 2)  # lunes
WEEKEND_HEAVY = [0.5, 0.5, 0.5, 0.5, 1.0, 2.0, 2.0]


def _rows(same_type: bool, factors: list[float], businesses: int):
    return [(same_type, weekday, factor, businesses) for weekday, factor in enumerate(factors)]


def test_prior_needs_minimum_businesses_for_anonymity():
    assert pooled_prior(_rows(True, WEEKEND_HEAVY, MIN_POOL_BUSINESSES - 1)) is None
    assert pooled_prior(_rows(True, WEEKEND_HEAVY, MIN_POOL_BUSINESSES)) == WEEKEND_HEAVY
    assert pooled_prior([]) is None


def test_prior_prefers_same_business_type_and_falls_back_to_all():
    flat = [1.0] * 7
    rows = _rows(True, WEEKEND_HEAVY, 3) + _rows(False, flat, 3)
    assert pooled_prior(rows) == WEEKEND_HEAVY
    # Segmento propio muy pequeño: se combinan todos, ponderados por número de negocios.
    rows = _rows(True, WEEKEND_HEAVY, 1) + _rows(False, flat, 3)
    assert pooled_prior(rows) == [(w * 1 + 1.0 * 3) / 4 for w in WEEKEND_HEAVY]


def test_short_history_shrinks_towards_prior_instead_of_flat():
    daily = [10.0] * 7  # una semana plana: un solo dato por día de la semana
    _, without = weekday_factors(daily, START)
    _, with_prior = weekday_factors(daily, START, WEEKEND_HEAVY)
    assert without == [1.0] * 7
    assert with_prior[5] > 1.0 > with_prior[0]  # el sábado sube y el lunes baja hacia el patrón agregado


def test_no_prior_keeps_previous_behaviour():
    daily = [5.0] * 45
    assert forecast(daily, 7, "AUTO", START) == forecast(daily, 7, "AUTO", START, None)
