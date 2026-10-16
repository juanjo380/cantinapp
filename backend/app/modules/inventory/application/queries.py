"""Consultas de inventario."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class ListInventoryQuery(Query):
    business_id: UUID
    status: str | None = None
    category: str | None = None
    search: str | None = None
    sort: str = "name"
    limit: int = 50
    offset: int = 0


@dataclass
class GetInventoryQuery(Query):
    business_id: UUID
    product_id: UUID


@dataclass
class ListMovementsQuery(Query):
    business_id: UUID
    product_id: UUID
    limit: int = 50
    offset: int = 0
