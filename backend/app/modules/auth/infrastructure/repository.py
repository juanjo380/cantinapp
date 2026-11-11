"""Adaptadores SQLAlchemy para los puertos de autenticación."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import PROFILE_REQUIRED_FIELDS, Business, EmailCode, Membership, User
from app.modules.auth.domain.repository import BusinessRepository, MembershipRepository, UserRepository
from app.modules.auth.infrastructure.models import (
    BusinessRecord,
    ConsentRecord,
    EmailCodeRecord,
    MembershipRecord,
    UserRecord,
)

USER_PROFILE_FIELDS = ("full_name", "phone", "job_title")


def _to_user(record: UserRecord) -> User:
    return User(
        id=record.id,
        business_id=record.business_id,
        email=record.email,
        full_name=record.full_name,
        is_active=record.is_active,
        phone=record.phone,
        job_title=record.job_title,
    )


class SqlUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _by_email(self, email: str) -> UserRecord | None:
        return (
            await self.session.execute(select(UserRecord).where(func.lower(UserRecord.email) == email.lower()))
        ).scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        record = await self._by_email(email)
        return _to_user(record) if record else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        record = await self.session.get(UserRecord, user_id)
        return _to_user(record) if record else None

    async def get_credentials(self, email: str) -> tuple[User, str] | None:
        record = await self._by_email(email)
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

    async def add_consents(
        self, *, business_id: UUID, user_id: UUID, version: str, consents: dict[str, bool]
    ) -> None:
        self.session.add_all(
            ConsentRecord(
                business_id=business_id, user_id=user_id, document=doc, version=version, granted=granted
            )
            for doc, granted in consents.items()
        )
        await self.session.flush()

    async def update_profile(self, user_id: UUID, changes: dict) -> User:
        record = await self.session.get(UserRecord, user_id)
        for name in USER_PROFILE_FIELDS:
            if name in changes:
                setattr(record, name, changes[name])
        await self.session.flush()
        return _to_user(record)

    async def set_password(self, user_id: UUID, password_hash: str) -> None:
        record = await self.session.get(UserRecord, user_id)
        record.password_hash = password_hash
        record.password_changed_at = datetime.now(UTC)
        await self.session.flush()

    async def set_last_business(self, user_id: UUID, business_id: UUID) -> None:
        record = await self.session.get(UserRecord, user_id)
        record.business_id = business_id
        await self.session.flush()

    async def add_code(self, *, user_id: UUID, purpose: str, code_hash: str, expires_at: datetime) -> None:
        self.session.add(EmailCodeRecord(user_id=user_id, purpose=purpose, code_hash=code_hash, expires_at=expires_at))
        await self.session.flush()

    async def latest_code(self, user_id: UUID, purpose: str) -> EmailCode | None:
        record = (
            await self.session.execute(
                select(EmailCodeRecord)
                .where(EmailCodeRecord.user_id == user_id, EmailCodeRecord.purpose == purpose)
                .order_by(EmailCodeRecord.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if record is None:
            return None
        return EmailCode(
            id=record.id,
            code_hash=record.code_hash,
            attempts=record.attempts,
            expires_at=record.expires_at,
            created_at=record.created_at,
            used_at=record.used_at,
        )

    async def count_code_attempt(self, code_id: UUID) -> None:
        await self.session.execute(
            update(EmailCodeRecord).where(EmailCodeRecord.id == code_id).values(attempts=EmailCodeRecord.attempts + 1)
        )

    async def use_code(self, code_id: UUID) -> None:
        await self.session.execute(
            update(EmailCodeRecord).where(EmailCodeRecord.id == code_id).values(used_at=func.now())
        )


class SqlBusinessRepository(BusinessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, name: str) -> Business:
        record = BusinessRecord(name=name)
        self.session.add(record)
        await self.session.flush()
        return Business(id=record.id, name=record.name)


class SqlMembershipRepository(MembershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, *, business_id: UUID, user_id: UUID, role: str) -> None:
        self.session.add(MembershipRecord(business_id=business_id, user_id=user_id, role=role))
        await self.session.flush()

    async def list_for_user(self, user_id: UUID) -> list[Membership]:
        rows = (
            await self.session.execute(
                select(MembershipRecord.role, MembershipRecord.location_id, BusinessRecord)
                .join(BusinessRecord, BusinessRecord.id == MembershipRecord.business_id)
                .where(MembershipRecord.user_id == user_id)
                .order_by(func.lower(BusinessRecord.name))
            )
        ).all()
        return [
            Membership(
                business_id=business.id,
                business_name=business.name,
                role=role,
                profile_completed=all(getattr(business, f) for f in PROFILE_REQUIRED_FIELDS),
                location_id=None if role == "OWNER" else location_id,
            )
            for role, location_id, business in rows
        ]
