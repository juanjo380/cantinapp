"""Comandos del módulo de autenticación."""
from dataclasses import dataclass, field

from app.shared.application.cqrs import Command


@dataclass
class RegisterCommand(Command):
    business_name: str
    email: str
    password: str
    full_name: str | None = None
    consents: dict[str, bool] = field(default_factory=dict)  # documento -> aceptado


@dataclass
class LoginCommand(Command):
    email: str
    password: str
