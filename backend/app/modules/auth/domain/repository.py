"""Puertos (interfaces) del dominio de autenticación."""
from typing import Protocol
from uuid import UUID

from app.modules.auth.domain.entities import Business, User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def get_password_hash(self, email: str) -> str | None: ...

    async def add(
        self, *, business_id: UUID, email: str, password_hash: str, full_name: str | None
    ) -> User: ...


class BusinessRepository(Protocol):
    async def add(self, name: str) -> Business: ...
