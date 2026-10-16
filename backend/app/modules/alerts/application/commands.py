"""Comandos del módulo de alertas (RF-15)."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class GenerateAlertsCommand(Command):
    business_id: UUID


@dataclass
class ReviewAlertCommand(Command):
    business_id: UUID
    alert_id: UUID
    user_id: UUID
