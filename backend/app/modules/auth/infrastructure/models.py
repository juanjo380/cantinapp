"""Modelos ORM de autenticación (businesses, users, user_consents, business_members, email_codes)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class BusinessRecord(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    # Perfil (migración 003); lo edita el módulo business
    legal_name: Mapped[str | None]
    tax_id: Mapped[str | None]
    business_type: Mapped[str | None]
    phone: Mapped[str | None]
    email: Mapped[str | None]
    address: Mapped[str | None]
    city: Mapped[str | None]
    department: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)  # último negocio usado
    email: Mapped[str]
    password_hash: Mapped[str]
    full_name: Mapped[str | None]
    phone: Mapped[str | None]
    job_title: Mapped[str | None]
    role: Mapped[str] = mapped_column(default="ADMIN")  # obsoleto: el rol real está en business_members
    is_active: Mapped[bool] = mapped_column(default=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # migración 004
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MembershipRecord(Base):
    __tablename__ = "business_members"

    business_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    role: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ConsentRecord(Base):
    __tablename__ = "user_consents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    document: Mapped[str]
    version: Mapped[str]
    granted: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class EmailCodeRecord(Base):
    __tablename__ = "email_codes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    purpose: Mapped[str]
    code_hash: Mapped[str]
    attempts: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
