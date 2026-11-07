"""Puertos (interfaces) del dominio de autenticación."""
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.auth.domain.entities import Business, EmailCode, Membership, User


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

    async def set_password(self, user_id: UUID, password_hash: str) -> None:
        """También marca password_changed_at: los tokens emitidos antes dejan de valer."""
        ...

    async def set_last_business(self, user_id: UUID, business_id: UUID) -> None: ...

    async def add_code(self, *, user_id: UUID, purpose: str, code_hash: str, expires_at: datetime) -> None: ...

    async def latest_code(self, user_id: UUID, purpose: str) -> EmailCode | None:
        """Solo vale el último código pedido: pedir otro anula los anteriores."""
        ...

    async def count_code_attempt(self, code_id: UUID) -> None: ...

    async def use_code(self, code_id: UUID) -> None: ...


class BusinessRepository(Protocol):
    async def add(self, name: str) -> Business: ...


class MembershipRepository(Protocol):
    async def add(self, *, business_id: UUID, user_id: UUID, role: str) -> None: ...

    async def list_for_user(self, user_id: UUID) -> list[Membership]: ...
