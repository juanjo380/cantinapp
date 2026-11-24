from decimal import Decimal
from uuid import uuid4

from app.modules.products.domain.discounts import (
    DiscountCandidate,
    discount_percent,
    discounted_price,
    suggest_discounts,
)


def _c(units, stock=10, price="5000", recent=False):
    return DiscountCandidate(uuid4(), f"p{units}", None, Decimal(price), stock, units, None, recent)


def test_flags_only_products_70pct_below_average():
    # promedio = (100 + 100 + 20 + 0) / 4 = 55 → umbral 16.5
    rows = [_c(100), _c(100), _c(20), _c(0)]
    result = suggest_discounts(rows, window_days=30)
    assert [s.units for s in result] == [0]
    assert result[0].percent == 30 and result[0].suggested_price == Decimal(3500)
    assert result[0].coverage_days is None


def test_tiers_by_ratio():
    rows = [_c(100)] * 8 + [_c(10), _c(5)]  # promedio 81.5: 10 → 12 % (20 %), 5 → 6 % (20 %)
    percents = {s.units: s.percent for s in suggest_discounts(rows, window_days=30)}
    assert percents == {10: 20, 5: 20}
    rows = [_c(100)] * 8 + [_c(20)]  # promedio ≈ 91: 20 → 22 % (10 %)
    assert [s.percent for s in suggest_discounts(rows, window_days=30)] == [10]


def test_skips_out_of_stock_recent_and_no_sales_business():
    assert suggest_discounts([_c(100), _c(0, stock=0), _c(0, recent=True)], window_days=30) == []
    assert suggest_discounts([_c(0), _c(0)], window_days=30) == []


def test_price_rounding_and_no_op_discount():
    assert discounted_price(Decimal("2490"), 10) == Decimal(2250)
    assert suggest_discounts([_c(100), _c(0, price="50")], window_days=30) == []  # 35 → 50: no baja


def test_discount_percent_from_list_price():
    assert discount_percent(Decimal(5000), Decimal(3500)) == 30
    assert discount_percent(Decimal(2490), Decimal(2250)) == 10  # 9.6 % por el redondeo
