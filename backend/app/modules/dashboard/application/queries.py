"""Consulta del dashboard."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class DashboardQuery(Query):
    business_id: UUID
    trend_days: int = 30
    location_id: UUID | None = None  # ventas de una sede; el stock es del negocio
