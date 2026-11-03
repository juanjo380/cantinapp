"""Modelo ORM de sedes. Negocio, usuarios y miembros viven en auth/infrastructure/models.py."""
import uuid
from datetime import datetime

from sqlalchemy import Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.base_model import Base


class LocationRecord(Base):
    __tablename__ = "business_locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    name: Mapped[str]
    address: Mapped[str | None]
    city: Mapped[str | None]
    phone: Mapped[str | None]
    is_main: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
