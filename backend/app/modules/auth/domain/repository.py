"""Puertos (interfaces) del dominio de autenticación."""
from typing import Protocol
from uuid import UUID

from app.modules.auth.domain.entities import Business, Membership, User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_credentials(self, email: str) -> tuple[User, str] | None:
        """Usuario y hash de contraseña en una sola consulta (login)."""
        ...

    async def add(
        self, *, business_id: UUID, email: str, password_hash: str, full_name: str | None
    ) -> User: ...

    async def add_consents(
        self, *, business_id: UUID, user_id: UUID, version: str, consents: dict[str, bool]
    ) -> None:
        """Registra una fila por documento (prueba de la autorización, Ley 1581)."""
        ...

    async def update_profile(self, user_id: UUID, changes: dict) -> User: ...

    async def set_password(self, user_id: UUID, password_hash: str) -> None: ...

    async def set_last_business(self, user_id: UUID, business_id: UUID) -> None: ...


class BusinessRepository(Protocol):
    async def add(self, name: str) -> Business: ...


class MembershipRepository(Protocol):
    async def add(self, *, business_id: UUID, user_id: UUID, role: str) -> None: ...

    async def list_for_user(self, user_id: UUID) -> list[Membership]: ...
