"""Comandos del módulo de negocio. `actor` es el usuario que actúa (con su rol en el negocio)."""
from dataclasses import dataclass
from uuid import UUID

from app.shared.api.dependencies import CurrentUser
from app.shared.application.cqrs import Command


@dataclass
class UpdateBusinessCommand(Command):
    actor: CurrentUser
    changes: dict


@dataclass
class SaveLocationCommand(Command):
    actor: CurrentUser
    location_id: UUID | None  # None = crear
    data: dict


@dataclass
class InviteMemberCommand(Command):
    actor: CurrentUser
    email: str
    role: str


@dataclass
class AcceptInvitationCommand(Command):
    """Lo ejecuta la persona invitada con su sesión: aún no es miembro del negocio."""

    user_id: UUID
    email: str
    token: str
    code: str


@dataclass
class ChangeRoleCommand(Command):
    actor: CurrentUser
    user_id: UUID
    role: str


@dataclass
class RemoveMemberCommand(Command):
    actor: CurrentUser
    user_id: UUID
