"""Comandos de inventario (reposiciones y ajustes manuales)."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class RegisterMovementCommand(Command):
    business_id: UUID
    product_id: UUID
    movement_type: str
    quantity_change: int
    notes: str | None
    created_by: UUID
