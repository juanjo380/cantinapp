"""Comandos del módulo de predicción (RF-12)."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class RunForecastCommand(Command):
    business_id: UUID
    product_id: UUID
    forecast_days: int
    model: str
    created_by: UUID
