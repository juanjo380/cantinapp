"""Consultas de análisis."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class SalesSeriesQuery(Query):
    business_id: UUID
    period: str
    date_from: date
    date_to: date
    product_id: UUID | None = None


@dataclass
class ProductRankingQuery(Query):
    business_id: UUID
    order: str
    limit: int
    date_from: date
    date_to: date
