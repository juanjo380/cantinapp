"""Consulta del dashboard."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Query


@dataclass
class DashboardQuery(Query):
    business_id: UUID
    trend_days: int = 30
