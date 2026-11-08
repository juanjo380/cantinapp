"""Datos de ejemplo de una cantina/tienda (lógica pura y determinista).

90 días de ventas con:
- patrón semanal (viernes y sábado fuertes, domingo flojo),
- quincena (días 15 y último del mes venden más),
- picos esporádicos de empanadas seguidos de más gaseosa al día siguiente, para que la
  co-ocurrencia encuentre una relación real,
- algunos productos con stock bajo o agotado, para que haya alertas desde el inicio.

Los nombres llevan el sufijo «(ejemplo)» para reconocerlos a simple vista.
"""
import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

SUFFIX = " (ejemplo)"
DAYS = 90
_WEEKDAY = (1.0, 0.95, 1.0, 1.05, 1.35, 1.2, 0.6)  # lunes..domingo
_PAYDAY_BOOST = 1.5
_SPIKE_DAYS = 7  # picos de empanadas en el periodo


@dataclass(frozen=True)
class DemoProduct:
    name: str
    category: str
    supplier: str
    price: Decimal
    stock: int
    min_stock: int
    lead_time_days: int
    daily_units: float  # promedio de un día normal


@dataclass(frozen=True)
class DemoSale:
    product: int  # índice en la lista de productos
    sale_date: date
    quantity: int
    unit_price: Decimal


_CATALOG = [
    ("Empanada", "Comidas", "Panadería La Espiga", "2500", 40, 30, 1, 22),
    ("Gaseosa 400 ml", "Bebidas", "Distribuidora Central", "3200", 48, 24, 3, 14),
    ("Agua 600 ml", "Bebidas", "Distribuidora Central", "2000", 30, 12, 3, 8),
    ("Jugo en caja", "Bebidas", "Distribuidora Central", "2200", 6, 15, 3, 9),
    ("Café tinto", "Bebidas calientes", "Café del Valle", "1500", 200, 50, 7, 18),
    ("Pan de bono", "Comidas", "Panadería La Espiga", "1800", 12, 20, 1, 15),
    ("Arepa con queso", "Comidas", "Panadería La Espiga", "3000", 25, 10, 1, 9),
    ("Papas fritas paquete", "Paquetes", "Snacks S.A.", "2800", 0, 12, 5, 7),
    ("Galletas de avena", "Paquetes", "Snacks S.A.", "1800", 40, 10, 5, 6),
    ("Chocolatina", "Dulces", "Dulces La Fe", "1200", 60, 20, 5, 11),
    ("Bocadillo", "Dulces", "Dulces La Fe", "800", 50, 15, 7, 5),
    ("Yogur", "Lácteos", "Lácteos Andinos", "2600", 8, 10, 2, 5),
]
_EMPANADA, _GASEOSA = 0, 1


def products() -> list[DemoProduct]:
    return [
        DemoProduct(f"{name}{SUFFIX}", category, supplier, Decimal(price), stock, min_stock, lead, units)
        for name, category, supplier, price, stock, min_stock, lead, units in _CATALOG
    ]


def _is_payday(day: date) -> bool:
    return day.day == 15 or (day + timedelta(days=1)).month != day.month


def sales(today: date, seed: int = 2026) -> list[DemoSale]:
    """Ventas de los 90 días anteriores a `today` (incluido). Misma semilla = mismos datos."""
    rng = random.Random(seed)
    catalog = products()
    first = today - timedelta(days=DAYS - 1)
    spike_days = set(rng.sample(range(14, DAYS - 1), _SPIKE_DAYS))  # tras 14 días: hay base para comparar
    result: list[DemoSale] = []
    for offset in range(DAYS):
        day = first + timedelta(days=offset)
        boost = _WEEKDAY[day.weekday()] * (_PAYDAY_BOOST if _is_payday(day) else 1.0)
        for index, product in enumerate(catalog):
            units = product.daily_units * boost * rng.gauss(1.0, 0.15)
            if index == _EMPANADA and offset in spike_days:
                units *= 3
            if index == _GASEOSA and offset - 1 in spike_days:
                units *= 2
            quantity = round(units)
            if quantity > 0:
                result.append(DemoSale(index, day, quantity, product.price))
    return result
