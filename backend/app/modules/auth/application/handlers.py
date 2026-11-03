"""Handlers de los casos de uso de autenticación."""
import asyncio
import time
from functools import cache
from uuid import UUID

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableError,
)
from app.core.security import hash_password, verify_password
from app.modules.auth.application.commands import (
    ChangePasswordCommand,
    CreateBusinessCommand,
    LoginCommand,
    RegisterCommand,
    SwitchBusinessCommand,
    UpdateProfileCommand,
)
from app.modules.auth.domain.entities import Business, Session, User, build_session
from app.modules.auth.domain.repository import BusinessRepository, MembershipRepository, UserRepository

# Debe coincidir con la fecha `UPDATED` de frontend/src/components/auth/LegalDialog.jsx.
LEGAL_VERSION = "2026-11-01"
# La política de cookies forma parte de la de privacidad (PRIVACY) desde 2026-11-02.
REQUIRED_CONSENTS = ("TERMS", "PRIVACY")
OPTIONAL_CONSENTS = ("ML_ANONYMOUS",)

_MAX_FAILED_LOGINS = 5
_LOCKOUT_SECONDS = 15 * 60
# shortcut: contador en memoria por proceso; con varias instancias moverlo a Redis o a una tabla.
_failed_logins: dict[str, list[float]] = {}


@cache
def _dummy_hash() -> str:
    return hash_password("usuario-inexistente")


def _recent_failures(email: str) -> list[float]:
    now = time.monotonic()
    attempts = [t for t in _failed_logins.get(email, []) if now - t < _LOCKOUT_SECONDS]
    if attempts:
        _failed_logins[email] = attempts
    else:
        _failed_logins.pop(email, None)
    return attempts


def _register_failure(email: str) -> None:
    if len(_failed_logins) > 10_000:  # evita que emails aleatorios llenen la memoria
        _failed_logins.clear()
    _failed_logins.setdefault(email, []).append(time.monotonic())


async def register_user(
    users: UserRepository,
    businesses: BusinessRepository,
    memberships: MembershipRepository,
    command: RegisterCommand,
) -> tuple[User, Business]:
    """RF-01: crea negocio + usuario dueño con email único y guarda sus autorizaciones."""
    if not all(command.consents.get(doc) for doc in REQUIRED_CONSENTS):
        raise UnprocessableError(
            "Debes aceptar los términos y condiciones y la política de privacidad y cookies"
        )
    if await users.get_by_email(command.email) is not None:
        raise ConflictError("El email ya está registrado")
    # PBKDF2 es CPU puro: en un hilo para no bloquear el event loop.
    password_hash = await asyncio.to_thread(hash_password, command.password)
    business = await businesses.add(command.business_name.strip())
    user = await users.add(
        business_id=business.id,
        email=command.email.strip().lower(),
        password_hash=password_hash,
        full_name=command.full_name,
    )
    await memberships.add(business_id=business.id, user_id=user.id, role="OWNER")
    await users.add_consents(
        business_id=business.id,
        user_id=user.id,
        version=LEGAL_VERSION,
        consents={doc: bool(command.consents.get(doc)) for doc in REQUIRED_CONSENTS + OPTIONAL_CONSENTS},
    )
    return user, business


async def authenticate(users: UserRepository, command: LoginCommand) -> User:
    """RF-02: valida credenciales, con bloqueo temporal tras varios fallos."""
    email = command.email.strip().lower()
    attempts = _recent_failures(email)
    if len(attempts) >= _MAX_FAILED_LOGINS:
        minutes = max(1, int((_LOCKOUT_SECONDS - (time.monotonic() - attempts[0])) // 60) + 1)
        raise TooManyRequestsError(f"Demasiados intentos fallidos. Inténtalo de nuevo en {minutes} min.")

    found = await users.get_credentials(email)
    # Con email inexistente se verifica contra un hash falso: mismo tiempo de respuesta, sin enumerar usuarios.
    stored = found[1] if found else _dummy_hash()
    valid = await asyncio.to_thread(verify_password, command.password, stored)
    if not found or not valid:
        _register_failure(email)
        raise UnauthorizedError("Correo o contraseña incorrectos")
    user = found[0]
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    _failed_logins.pop(email, None)
    return user


async def load_session(
    users: UserRepository, memberships: MembershipRepository, user_id: UUID, preferred: list[UUID | None]
) -> Session:
    user = await users.get_by_id(user_id)
    return build_session(user, await memberships.list_for_user(user_id), preferred)


async def login_session(users: UserRepository, memberships: MembershipRepository, user: User) -> Session:
    """Abre el último negocio usado; si ya no es miembro, el primero de su lista (o ninguno)."""
    found = await memberships.list_for_user(user.id)
    return build_session(user, found, [user.business_id, *(m.business_id for m in found[:1])])


async def switch_business(
    users: UserRepository, memberships: MembershipRepository, command: SwitchBusinessCommand
) -> Session:
    session = await load_session(users, memberships, command.user_id, [command.business_id])
    if session.business_id != command.business_id:
        raise NotFoundError("Negocio no encontrado")  # no revela negocios ajenos
    await users.set_last_business(command.user_id, command.business_id)
    return session


async def create_business(
    users: UserRepository,
    businesses: BusinessRepository,
    memberships: MembershipRepository,
    command: CreateBusinessCommand,
) -> Session:
    business = await businesses.add(command.name.strip())
    await memberships.add(business_id=business.id, user_id=command.user_id, role="OWNER")
    await users.set_last_business(command.user_id, business.id)
    return await load_session(users, memberships, command.user_id, [business.id])


async def update_profile(users: UserRepository, command: UpdateProfileCommand) -> User:
    return await users.update_profile(command.user_id, command.changes)


async def change_password(users: UserRepository, command: ChangePasswordCommand) -> None:
    found = await users.get_credentials(command.email)
    valid = found is not None and await asyncio.to_thread(verify_password, command.current_password, found[1])
    if not valid:
        # 422, no 401: un 401 haría que el cliente cierre la sesión.
        raise UnprocessableError("La contraseña actual no es correcta")
    await users.set_password(command.user_id, await asyncio.to_thread(hash_password, command.new_password))
