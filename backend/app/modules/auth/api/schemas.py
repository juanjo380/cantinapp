"""Esquemas HTTP del módulo de autenticación."""
import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = r"^\+?[\d\s()-]{7,20}$"


class _EmailMixin(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("email inválido")
        return value


class RegisterRequest(_EmailMixin):
    business_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)
    # Autorizaciones del registro (términos y privacidad son obligatorias; se valida en el handler).
    accept_terms: bool = False
    accept_privacy: bool = False  # incluye la política de cookies
    allow_ml_data: bool = False


class LoginRequest(_EmailMixin):
    password: str = Field(min_length=1, max_length=128)


class SwitchBusinessRequest(BaseModel):
    business_id: UUID


class CreateBusinessRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    job_title: str | None = Field(default=None, max_length=100)

    @field_validator("full_name", "job_title", "phone", mode="before")
    @classmethod
    def _blank_is_none(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: UUID
    business_id: UUID | None  # negocio activo de la sesión
    email: str
    full_name: str | None
    phone: str | None = None
    job_title: str | None = None


class MembershipOut(BaseModel):
    business_id: UUID
    business_name: str
    role: str
    profile_completed: bool


class SessionOut(BaseModel):
    user: UserOut
    business_id: UUID | None
    business_name: str | None = None
    role: str | None = None  # OWNER | ADMIN | MEMBER en el negocio activo
    profile_completed: bool = False
    businesses: list[MembershipOut] = []


class AuthResponse(SessionOut):
    token: str
    token_type: str = "bearer"
