"""Esquemas HTTP del módulo de análisis."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SeriesPointOut(BaseModel):
    period: date
    units: int
    revenue: Decimal


class SalesSeriesOut(BaseModel):
    period: str
    date_from: date
    date_to: date
    series: list[SeriesPointOut]


class ProductRankingOut(BaseModel):
    product_id: UUID
    name: str
    units: int
    revenue: Decimal


class ProductRankingListOut(BaseModel):
    order: str
    items: list[ProductRankingOut]
