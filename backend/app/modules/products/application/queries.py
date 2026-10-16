"""Consultas del módulo de productos."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class ListProductsQuery(Query):
    business_id: UUID
    search: str | None = None
    category: str | None = None
    active_only: bool = True
    sort: str = "name"
    limit: int = 50
    offset: int = 0


@dataclass
class GetProductQuery(Query):
    business_id: UUID
    product_id: UUID
