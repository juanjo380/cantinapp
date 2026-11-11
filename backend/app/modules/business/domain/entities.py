"""Dominio del negocio: perfil, sedes y equipo (miembros con rol)."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

BUSINESS_TYPES = (
    "TIENDA", "MINIMERCADO", "CANTINA_ESCOLAR", "CAFETERIA", "RESTAURANTE", "PANADERIA", "DROGUERIA", "OTRO",
)
PROFILE_FIELDS = ("name", "legal_name", "tax_id", "business_type", "phone", "email", "address", "city", "department", "composites_enabled")
ASSIGNABLE_ROLES = ("ADMIN", "MEMBER")  # el dueño no se asigna: es quien crea el negocio

_NIT_WEIGHTS = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)


def nit_check_digit(number: str) -> int:
    """Dígito de verificación del NIT (DIAN, módulo 11)."""
    total = sum(int(d) * w for d, w in zip(reversed(number), _NIT_WEIGHTS))
    remainder = total % 11
    return remainder if remainder < 2 else 11 - remainder


def normalize_nit(value: str) -> str:
    """'900.123.456-8' -> '900123456-8'. Lanza ValueError si el formato o el dígito no cuadran."""
    clean = value.replace(".", "").replace(" ", "")
    number, _, dv = clean.partition("-")
    if not number.isdigit() or not 6 <= len(number) <= 15 or (dv and not (dv.isdigit() and len(dv) == 1)):
        raise ValueError("NIT inválido: usa solo números y, si quieres, el dígito de verificación (900123456-8)")
    if dv and int(dv) != nit_check_digit(number):
        raise ValueError("El dígito de verificación del NIT no corresponde")
    return f"{number}-{dv}" if dv else number


@dataclass
class BusinessProfile:
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
    composites_enabled: bool


@dataclass
class Location:
    id: UUID
    name: str
    address: str | None
    city: str | None
    phone: str | None
    is_main: bool


@dataclass
class Member:
    user_id: UUID
    email: str
    full_name: str | None
    job_title: str | None
    role: str
    created_at: datetime
    location_id: UUID | None = None  # sede asignada; None = todas


@dataclass
class Invitation:
    """Invitación vigente (sin aceptar ni anular). Los hashes solo los usa la aceptación."""

    id: UUID
    business_id: UUID
    business_name: str
    email: str
    role: str
    invited_by_name: str
    expires_at: datetime
    created_at: datetime
    code_hash: str = ""
    attempts: int = 0
    location_id: UUID | None = None
