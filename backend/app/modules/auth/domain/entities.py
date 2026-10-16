"""Entidades del dominio de autenticación."""
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Business:
    id: UUID
    name: str


@dataclass
class User:
    id: UUID
    business_id: UUID
    email: str
    full_name: str | None
    is_active: bool
