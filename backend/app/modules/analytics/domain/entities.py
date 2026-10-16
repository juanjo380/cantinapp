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
