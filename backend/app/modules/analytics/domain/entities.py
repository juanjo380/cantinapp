"""Entidades del dominio de análisis histórico."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

PERIOD_UNITS = {"daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"}


@dataclass
class SalesSeriesPoint:
    period: date
    units: int
    revenue: Decimal


@dataclass
class ProductRanking:
    product_id: UUID
    name: str
    units: int
    revenue: Decimal


@dataclass
class ClassifiedProduct:
    product_id: UUID
    name: str
    units: int
    revenue: Decimal
    rank: int
    share: float  # parte de los ingresos del período (0..1)
    cumulative_share: float
    abc: str  # A: hacen el 80 % de los ingresos; B: el siguiente 15 %; C: el resto
    previous_rank: int | None  # puesto en el período anterior de igual duración


def abc_classify(current: list[ProductRanking], previous: list[ProductRanking]) -> list[ClassifiedProduct]:
    """Clasificación ABC (Pareto) por ingresos. Un producto es A si antes de sumarlo aún no se
    llegaba al 80 %: así el primero siempre es A aunque solo él pase del 80 %."""
    ordered = sorted(current, key=lambda p: (-p.revenue, -p.units, p.name))
    total = sum(p.revenue for p in ordered) or Decimal(1)
    before = {p.product_id: i + 1 for i, p in enumerate(sorted(previous, key=lambda p: (-p.revenue, -p.units, p.name)))}
    result, running = [], Decimal(0)
    for rank, p in enumerate(ordered, start=1):
        abc = "A" if running / total < Decimal("0.8") else "B" if running / total < Decimal("0.95") else "C"
        running += p.revenue
        result.append(
            ClassifiedProduct(
                product_id=p.product_id,
                name=p.name,
                units=p.units,
                revenue=p.revenue,
                rank=rank,
                share=round(float(p.revenue / total), 4),
                cumulative_share=round(float(running / total), 4),
                abc=abc,
                previous_rank=before.get(p.product_id),
            )
        )
    return result
