"""Adaptador SQLAlchemy del negocio. Reusa los modelos de auth (businesses, users, business_members)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.modules.auth.infrastructure.models import BusinessRecord, ConsentRecord, MembershipRecord, UserRecord
from app.modules.business.domain.entities import PROFILE_FIELDS, BusinessProfile, Invitation, Location, Member
from app.modules.business.domain.repository import BusinessProfileRepository
from app.modules.business.infrastructure.models import InvitationRecord, LocationRecord

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

    # --- invitaciones ---------------------------------------------------------

    def _invitations_query(self):
        inviter = aliased(UserRecord)
        return (
            select(InvitationRecord, BusinessRecord.name, func.coalesce(inviter.full_name, inviter.email))
            .join(BusinessRecord, BusinessRecord.id == InvitationRecord.business_id)
            .join(inviter, inviter.id == InvitationRecord.invited_by)
            .where(InvitationRecord.accepted_at.is_(None), InvitationRecord.revoked_at.is_(None))
        )

    @staticmethod
    def _to_invitation(record: InvitationRecord, business_name: str, inviter_name: str) -> Invitation:
        return Invitation(
            id=record.id,
            business_id=record.business_id,
            business_name=business_name,
            email=record.email,
            role=record.role,
            invited_by_name=inviter_name,
            expires_at=record.expires_at,
            created_at=record.created_at,
            code_hash=record.code_hash,
            attempts=record.attempts,
        )

    def _pending(self, business_id: UUID):
        return update(InvitationRecord).where(
            InvitationRecord.business_id == business_id,
            InvitationRecord.accepted_at.is_(None),
            InvitationRecord.revoked_at.is_(None),
        )

    async def add_invitation(
        self,
        *,
        business_id: UUID,
        email: str,
        role: str,
        invited_by: UUID,
        token_hash: str,
        code_hash: str,
        expires_at: datetime,
    ) -> Invitation:
        await self.session.execute(
            self._pending(business_id)
            .where(func.lower(InvitationRecord.email) == email.lower())
            .values(revoked_at=func.now())
        )
        record = InvitationRecord(
            business_id=business_id,
            email=email.lower(),
            role=role,
            invited_by=invited_by,
            token_hash=token_hash,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.flush()
        row = (await self.session.execute(self._invitations_query().where(InvitationRecord.id == record.id))).one()
        return self._to_invitation(*row)

    async def list_invitations(self, business_id: UUID) -> list[Invitation]:
        rows = (
            await self.session.execute(
                self._invitations_query()
                .where(InvitationRecord.business_id == business_id, InvitationRecord.expires_at > func.now())
                .order_by(InvitationRecord.created_at.desc())
            )
        ).all()
        return [self._to_invitation(*row) for row in rows]

    async def revoke_invitation(self, business_id: UUID, invitation_id: UUID) -> bool:
        result = await self.session.execute(
            self._pending(business_id).where(InvitationRecord.id == invitation_id).values(revoked_at=func.now())
        )
        return result.rowcount > 0

    async def find_invitation(self, token_hash: str) -> Invitation | None:
        row = (
            await self.session.execute(self._invitations_query().where(InvitationRecord.token_hash == token_hash))
        ).first()
        return self._to_invitation(*row) if row else None

    async def count_invitation_attempt(self, invitation_id: UUID) -> None:
        await self.session.execute(
            update(InvitationRecord)
            .where(InvitationRecord.id == invitation_id)
            .values(attempts=InvitationRecord.attempts + 1)
        )

    async def accept_invitation(self, invitation_id: UUID) -> None:
        await self.session.execute(
            update(InvitationRecord).where(InvitationRecord.id == invitation_id).values(accepted_at=func.now())
        )

    async def ml_data_sharing(self, business_id: UUID) -> bool:
        # Bitácora de solo inserción: manda la fila más reciente del negocio.
        granted = await self.session.scalar(
            select(ConsentRecord.granted)
            .where(ConsentRecord.business_id == business_id, ConsentRecord.document == "ML_ANONYMOUS")
            .order_by(ConsentRecord.created_at.desc())
            .limit(1)
        )
        return bool(granted)

    async def set_ml_data_sharing(self, business_id: UUID, user_id: UUID, granted: bool, version: str) -> None:
        self.session.add(
            ConsentRecord(
                business_id=business_id, user_id=user_id, document="ML_ANONYMOUS", version=version, granted=granted
            )
        )
        await self.session.flush()
