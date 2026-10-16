"""Comandos del módulo de autenticación."""
from dataclasses import dataclass

from app.shared.application.cqrs import Command


@dataclass
class RegisterCommand(Command):
    business_name: str
    email: str
    password: str
    full_name: str | None = None


@dataclass
class LoginCommand(Command):
    email: str
    password: str
