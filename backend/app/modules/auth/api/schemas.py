"""Esquemas HTTP del módulo de autenticación."""
import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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


class LoginRequest(_EmailMixin):
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: UUID
    business_id: UUID
    email: str
    full_name: str | None


class AuthResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserOut
    business_id: UUID
    business_name: str | None = None
