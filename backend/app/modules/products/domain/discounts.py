"""Sugerencias de descuento para productos de baja rotación. Lógica pura.

Un producto es candidato si en la ventana vendió menos del 30 % del promedio de
unidades por producto del negocio (≥ 70 % por debajo), lleva al menos esa ventana
en el catálogo, tiene stock, no tiene un descuento activo y no recibió uno dentro de la misma ventana.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

SLOW_RATIO = 0.3  # vende < 30 % del promedio
PRICE_STEP = Decimal(50)  # precios en COP redondeados a múltiplos de 50


@dataclass
class DiscountCandidate:
    product_id: UUID
    name: str
    category: str | None
    price: Decimal
    stock: int
    units: int  # vendidas en la ventana (incluye consumo como componente de compuestos)
    last_sale: date | None
    recently_discounted: bool  # descuento activo o aplicado dentro de la ventana


@dataclass
class DiscountSuggestion:
    product_id: UUID
    name: str
    category: str | None
    price: Decimal
    suggested_price: Decimal
    percent: int
    stock: int
    units: int
    business_avg: float
    coverage_days: float | None  # días que dura el stock al ritmo actual; None = sin ventas
    last_sale: date | None


@dataclass
class ActiveDiscount:
    product_id: UUID
    price_before: Decimal  # precio de lista
    percent: int
    discounted_at: datetime | None


def discount_percent(price_before: Decimal, price: Decimal) -> int:
    return round((1 - Decimal(price) / Decimal(price_before)) * 100) if price_before else 0


def discounted_price(price: Decimal, percent: int) -> Decimal:
    raw = Decimal(price) * (100 - percent) / 100
    return (raw / PRICE_STEP).to_integral_value(ROUND_HALF_UP) * PRICE_STEP


def suggest_discounts(candidates: list[DiscountCandidate], *, window_days: int) -> list[DiscountSuggestion]:
    # El promedio incluye a todos (también agotados y ya rebajados): son la referencia de lo que se vende.
    if not candidates:
        return []
    avg = sum(c.units for c in candidates) / len(candidates)
    if avg <= 0:
        return []  # sin ventas en la ventana no hay con qué comparar

    suggestions = []
    for c in candidates:
        ratio = c.units / avg
        if ratio >= SLOW_RATIO or c.stock <= 0 or c.recently_discounted or c.price <= 0:
            continue
        percent = 30 if c.units == 0 else 20 if ratio < 0.15 else 10
        new_price = discounted_price(c.price, percent)
        if new_price >= c.price:
            continue  # precio tan bajo que el redondeo anula el descuento
        daily = c.units / window_days
        suggestions.append(
            DiscountSuggestion(
                product_id=c.product_id,
                name=c.name,
                category=c.category,
                price=c.price,
                suggested_price=new_price,
                percent=percent,
                stock=c.stock,
                units=c.units,
                business_avg=round(avg, 2),
                coverage_days=round(c.stock / daily, 1) if daily else None,
                last_sale=c.last_sale,
            )
        )
    # Primero lo que más dinero tiene inmovilizado.
    return sorted(suggestions, key=lambda s: s.price * s.stock, reverse=True)
