"""Entidades del dominio de autenticación y pertenencia a negocios."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

ROLES = ("OWNER", "ADMIN", "MEMBER")
# Campos del negocio que deben estar llenos para dar el perfil por completo (más el nombre del usuario).
PROFILE_REQUIRED_FIELDS = ("business_type", "phone", "address", "city", "department")


@dataclass
class Business:
    id: UUID
    name: str


@dataclass
class User:
    id: UUID
    business_id: UUID | None  # último negocio usado
    email: str
    full_name: str | None
    is_active: bool
    phone: str | None = None
    job_title: str | None = None


@dataclass
class Membership:
    business_id: UUID
    business_name: str
    role: str
    profile_completed: bool
    location_id: UUID | None = None
    composites_enabled: bool = False  # sede asignada (None = todas)


@dataclass
class EmailCode:
    """Código de un solo uso enviado por correo (solo se conoce su hash)."""

    id: UUID
    code_hash: str
    attempts: int
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    def usable(self, now: datetime, max_attempts: int) -> bool:
        return self.used_at is None and self.attempts < max_attempts and now < self.expires_at


@dataclass
class Session:
    """Lo que el cliente necesita tras iniciar sesión: usuario, negocio activo y sus negocios."""

    user: User
    business_id: UUID | None = None
    business_name: str | None = None
    role: str | None = None
    profile_completed: bool = False
    composites_enabled: bool = False
    businesses: list[Membership] = field(default_factory=list)


def build_session(user: User, memberships: list[Membership], preferred: list[UUID | None]) -> Session:
    """Activa el primer negocio de `preferred` al que el usuario pertenezca; si ninguno, sin negocio."""
    by_id = {m.business_id: m for m in memberships}
    active = next((by_id[b] for b in preferred if b in by_id), None)
    if active is None:
        return Session(user=user, businesses=memberships)
    return Session(
        user=user,
        business_id=active.business_id,
        business_name=active.business_name,
        role=active.role,
        profile_completed=active.profile_completed and bool(user.full_name),
        composites_enabled=active.composites_enabled,
        businesses=memberships,
    )
