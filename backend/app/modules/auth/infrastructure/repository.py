"""Adaptadores SQLAlchemy para los puertos de autenticación."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import Business, User
from app.modules.auth.domain.repository import BusinessRepository, UserRepository
from app.modules.auth.infrastructure.models import BusinessRecord, UserRecord


def _to_user(record: UserRecord) -> User:
    return User(
        id=record.id,
        business_id=record.business_id,
        email=record.email,
        full_name=record.full_name,
        is_active=record.is_active,
    )


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        record = (
            await self.session.execute(
                select(UserRecord).where(func.lower(UserRecord.email) == email.lower())
            )
        ).scalar_one_or_none()
        return _to_user(record) if record else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        record = await self.session.get(UserRecord, user_id)
        return _to_user(record) if record else None

    async def get_credentials(self, email: str) -> tuple[User, str] | None:
        record = (
            await self.session.execute(
                select(UserRecord).where(func.lower(UserRecord.email) == email.lower())
            )
        ).scalar_one_or_none()
        return (_to_user(record), record.password_hash) if record else None

    async def add(
        self, *, business_id: UUID, email: str, password_hash: str, full_name: str | None
    ) -> User:
        record = UserRecord(
            business_id=business_id, email=email, password_hash=password_hash, full_name=full_name
        )
        self.session.add(record)
        await self.session.flush()
        return _to_user(record)


class SqlBusinessRepository(BusinessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, name: str) -> Business:
        record = BusinessRecord(name=name)
        self.session.add(record)
        await self.session.flush()
        return Business(id=record.id, name=record.name)
