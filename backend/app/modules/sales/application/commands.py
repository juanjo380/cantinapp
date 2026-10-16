"""Comandos del módulo de ventas (RF-06, RF-07)."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.shared.application.cqrs import Command


@dataclass
class CreateSaleCommand(Command):
    business_id: UUID
    product_id: UUID
    sale_date: date
    quantity: int
    unit_price: Decimal | None
    created_by: UUID


@dataclass
class ImportSalesCommand(Command):
    business_id: UUID
    file_name: str
    content: str
    affects_inventory: bool
    created_by: UUID
