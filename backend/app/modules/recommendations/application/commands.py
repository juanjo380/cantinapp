"""Comandos del módulo de recomendación (RF-13)."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class CreateRecommendationCommand(Command):
    business_id: UUID
    product_id: UUID
    forecast_days: int | None
    created_by: UUID


@dataclass
class RecomputeCoOccurrenceCommand(Command):
    business_id: UUID
