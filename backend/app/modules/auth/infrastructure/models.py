"""Modelos ORM de autenticación (tablas businesses y users)."""
import uuid
from datetime import datetime

from sqlalchemy import Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class BusinessRecord(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    email: Mapped[str]
    password_hash: Mapped[str]
    full_name: Mapped[str | None]
    role: Mapped[str] = mapped_column(default="ADMIN")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
