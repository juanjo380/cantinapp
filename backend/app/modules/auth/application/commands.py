"""Comandos del módulo de autenticación."""
from dataclasses import dataclass, field
from uuid import UUID

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


@dataclass
class SwitchBusinessCommand(Command):
    user_id: UUID
    business_id: UUID


@dataclass
class CreateBusinessCommand(Command):
    user_id: UUID
    name: str


@dataclass
class UpdateProfileCommand(Command):
    user_id: UUID
    changes: dict  # full_name, phone, job_title


@dataclass
class ChangePasswordCommand(Command):
    user_id: UUID
    email: str
    current_password: str
    new_password: str


@dataclass
class RequestPasswordResetCommand(Command):
    email: str


@dataclass
class ResetPasswordCommand(Command):
    email: str
    code: str
    new_password: str
