"""Entidades del dominio de autenticación y pertenencia a negocios."""
from dataclasses import dataclass, field
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


@dataclass
class Session:
    """Lo que el cliente necesita tras iniciar sesión: usuario, negocio activo y sus negocios."""

    user: User
    business_id: UUID | None = None
    business_name: str | None = None
    role: str | None = None
    profile_completed: bool = False
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
        businesses=memberships,
    )
