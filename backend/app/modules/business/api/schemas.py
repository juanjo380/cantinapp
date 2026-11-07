"""Esquemas HTTP del módulo de negocio."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.auth.api.schemas import _EMAIL_RE, PHONE_PATTERN
from app.modules.business.domain.entities import BUSINESS_TYPES, normalize_nit

BusinessType = Literal[BUSINESS_TYPES]
AssignableRole = Literal["ADMIN", "MEMBER"]


def _blank_is_none(value):
    return value.strip() or None if isinstance(value, str) else value


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    legal_name: str | None = Field(default=None, max_length=200)
    tax_id: str | None = Field(default=None, max_length=20)
    business_type: BusinessType | None = None
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    email: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)

    _blanks = field_validator(
        "legal_name", "tax_id", "business_type", "phone", "email", "address", "city", "department", mode="before"
    )(_blank_is_none)

    @field_validator("name")
    @classmethod
    def _name_required(cls, value):
        if value is None or not value.strip():
            raise ValueError("El nombre del negocio no puede quedar vacío")
        return value.strip()

    @field_validator("tax_id")
    @classmethod
    def _valid_nit(cls, value):
        return normalize_nit(value) if value else value

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value):
        if value and not _EMAIL_RE.match(value):
            raise ValueError("Correo inválido")
        return value.lower() if value else value


class BusinessOut(BaseModel):
    id: UUID
    name: str
    legal_name: str | None
    tax_id: str | None
    business_type: str | None
    phone: str | None
    email: str | None
    address: str | None
    city: str | None
    department: str | None


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    is_main: bool = False

    _blanks = field_validator("address", "city", "phone", mode="before")(_blank_is_none)


class LocationOut(BaseModel):
    id: UUID
    name: str
    address: str | None
    city: str | None
    phone: str | None
    is_main: bool


class InvitationCreate(BaseModel):
    email: str
    role: AssignableRole = "MEMBER"

    @field_validator("email")
    @classmethod
    def _valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Correo inválido")
        return value


class InvitationOut(BaseModel):
    id: UUID
    email: str
    role: str
    invited_by_name: str
    expires_at: datetime
    created_at: datetime


class InvitationCreated(InvitationOut):
    code: str  # código de seguridad: solo se devuelve al crear


class InvitationPreview(BaseModel):
    business_name: str
    role: str
    invited_by_name: str
    expires_at: datetime


class InvitationAccept(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    code: str = Field(pattern=r"^\d{6}$")


class RoleChange(BaseModel):
    role: AssignableRole


class MemberOut(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None
    job_title: str | None
    role: str
    created_at: datetime
