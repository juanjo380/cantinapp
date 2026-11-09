"""Clasificación ABC (Pareto) de productos por ingresos y cambio de puesto."""
from decimal import Decimal

from app.modules.analytics.domain.entities import ProductRanking, abc_classify


def _p(pid, revenue, units=1):
    return ProductRanking(product_id=pid, name=pid, units=units, revenue=Decimal(revenue))


def test_abc_by_revenue_share_and_rank_change():
    current = [_p("c", 50), _p("a", 700), _p("b", 150), _p("d", 100)]
    previous = [_p("a", 100), _p("b", 300)]
    result = abc_classify(current, previous)
    assert [(r.product_id, r.abc, r.rank) for r in result] == [("a", "A", 1), ("b", "A", 2), ("d", "B", 3), ("c", "C", 4)]
    assert result[0].share == 0.7 and result[-1].cumulative_share == 1.0
    assert [r.previous_rank for r in result] == [2, 1, None, None]


def test_single_dominant_product_is_a_and_empty_period_is_empty():
    assert [r.abc for r in abc_classify([_p("x", 990), _p("y", 10)], [])] == ["A", "C"]
    assert abc_classify([], []) == []
