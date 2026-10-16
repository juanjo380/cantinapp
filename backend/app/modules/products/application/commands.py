"""Comandos del módulo de productos (RF-04, RF-05)."""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class CreateProductCommand(Command):
    business_id: UUID
    name: str
    price: Decimal
    quantity: int
    min_stock: int
    lead_time_days: int
    category: str | None = None
    supplier: str | None = None


@dataclass
class UpdateProductCommand(Command):
    business_id: UUID
    product_id: UUID
    changes: dict
