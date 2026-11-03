"""Adaptador SQLAlchemy del negocio. Reusa los modelos de auth (businesses, users, business_members)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import BusinessRecord, MembershipRecord, UserRecord
from app.modules.business.domain.entities import PROFILE_FIELDS, BusinessProfile, Location, Member
from app.modules.business.domain.repository import BusinessProfileRepository
from app.modules.business.infrastructure.models import LocationRecord

_LOCATION_FIELDS = ("name", "address", "city", "phone", "is_main")


def _to_profile(record: BusinessRecord) -> BusinessProfile:
    return BusinessProfile(id=record.id, **{f: getattr(record, f) for f in PROFILE_FIELDS})


def _to_location(record: LocationRecord) -> Location:
    return Location(id=record.id, **{f: getattr(record, f) for f in _LOCATION_FIELDS})


class SqlBusinessProfileRepository(BusinessProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, business_id: UUID) -> BusinessProfile:
        return _to_profile(await self.session.get(BusinessRecord, business_id))

    async def update(self, business_id: UUID, changes: dict) -> BusinessProfile:
        record = await self.session.get(BusinessRecord, business_id)
        for name in PROFILE_FIELDS:
            if name in changes:
                setattr(record, name, changes[name])
        await self.session.flush()
        return _to_profile(record)

    async def list_locations(self, business_id: UUID) -> list[Location]:
        records = (
            await self.session.execute(
                select(LocationRecord)
                .where(LocationRecord.business_id == business_id)
                .order_by(LocationRecord.is_main.desc(), func.lower(LocationRecord.name))
            )
        ).scalars()
        return [_to_location(r) for r in records]

    async def _location(self, business_id: UUID, location_id: UUID) -> LocationRecord | None:
        record = await self.session.get(LocationRecord, location_id)
        return record if record and record.business_id == business_id else None

    async def get_location(self, business_id: UUID, location_id: UUID) -> Location | None:
        record = await self._location(business_id, location_id)
        return _to_location(record) if record else None

    async def save_location(self, business_id: UUID, location_id: UUID | None, data: dict) -> Location:
        if data.get("is_main"):
            # Antes de marcar la nueva: el índice único solo admite una sede principal.
            await self.session.execute(
                update(LocationRecord)
                .where(LocationRecord.business_id == business_id, LocationRecord.is_main.is_(True))
                .values(is_main=False)
            )
        record = await self._location(business_id, location_id) if location_id else None
        if record is None:
            record = LocationRecord(business_id=business_id)
            self.session.add(record)
        for name in _LOCATION_FIELDS:
            setattr(record, name, data.get(name, False if name == "is_main" else None))
        await self.session.flush()
        return _to_location(record)

    async def delete_location(self, business_id: UUID, location_id: UUID) -> None:
        await self.session.execute(
            delete(LocationRecord).where(LocationRecord.business_id == business_id, LocationRecord.id == location_id)
        )

    def _members_query(self, business_id: UUID):
        return (
            select(MembershipRecord, UserRecord)
            .join(UserRecord, UserRecord.id == MembershipRecord.user_id)
            .where(MembershipRecord.business_id == business_id)
        )

    @staticmethod
    def _to_member(membership: MembershipRecord, user: UserRecord) -> Member:
        return Member(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            job_title=user.job_title,
            role=membership.role,
            created_at=membership.created_at,
        )

    async def list_members(self, business_id: UUID) -> list[Member]:
        rows = (await self.session.execute(self._members_query(business_id).order_by(MembershipRecord.created_at))).all()
        return [self._to_member(*row) for row in rows]

    async def get_member(self, business_id: UUID, user_id: UUID) -> Member | None:
        row = (
            await self.session.execute(self._members_query(business_id).where(MembershipRecord.user_id == user_id))
        ).first()
        return self._to_member(*row) if row else None

    async def find_user_id(self, email: str) -> UUID | None:
        return (
            await self.session.execute(
                select(UserRecord.id).where(func.lower(UserRecord.email) == email.lower(), UserRecord.is_active)
            )
        ).scalar_one_or_none()

    async def add_member(self, business_id: UUID, user_id: UUID, role: str) -> None:
        self.session.add(MembershipRecord(business_id=business_id, user_id=user_id, role=role))
        await self.session.flush()

    async def set_role(self, business_id: UUID, user_id: UUID, role: str) -> None:
        await self.session.execute(
            update(MembershipRecord)
            .where(MembershipRecord.business_id == business_id, MembershipRecord.user_id == user_id)
            .values(role=role)
        )

    async def remove_member(self, business_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            delete(MembershipRecord).where(
                MembershipRecord.business_id == business_id, MembershipRecord.user_id == user_id
            )
        )
