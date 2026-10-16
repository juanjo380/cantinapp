"""Consultas del módulo de alertas."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class ListAlertsQuery(Query):
    business_id: UUID
    status: str | None = None
    limit: int = 50
    offset: int = 0
