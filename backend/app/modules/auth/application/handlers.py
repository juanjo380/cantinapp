"""Handlers de los casos de uso de autenticación."""
import asyncio
import time
from datetime import UTC, datetime, timedelta
from functools import cache
from uuid import UUID

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableError,
)
from app.core.security import MAX_CODE_ATTEMPTS, hash_password, hash_secret, new_code, same_secret, verify_password
from app.modules.auth.application.commands import (
    ChangePasswordCommand,
    CreateBusinessCommand,
    LoginCommand,
    RegisterCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
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

PASSWORD_RESET = "PASSWORD_RESET"
RESET_CODE_MINUTES = 5
RESET_RESEND_SECONDS = 60  # no se manda otro código antes de esto
INVALID_CODE = "El código no es válido o ya venció. Pide uno nuevo."

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


async def request_password_reset(users: UserRepository, command: RequestPasswordResetCommand) -> str | None:
    """Crea el código a enviar; None si no hay que enviar nada (cuenta inexistente o pedido repetido).
    La respuesta al cliente es la misma en ambos casos."""
    user = await users.get_by_email(command.email)
    if user is None or not user.is_active:
        return None
    now = datetime.now(UTC)
    last = await users.latest_code(user.id, PASSWORD_RESET)
    if last and (now - last.created_at).total_seconds() < RESET_RESEND_SECONDS:
        return None  # el código anterior sigue sirviendo
    code = new_code()
    await users.add_code(
        user_id=user.id,
        purpose=PASSWORD_RESET,
        code_hash=hash_secret(code),
        expires_at=now + timedelta(minutes=RESET_CODE_MINUTES),
    )
    return code


async def reset_password(users: UserRepository, command: ResetPasswordCommand) -> User:
    """Cambia la contraseña con el código del correo. El que llama debe confirmar la transacción
    aunque esto falle: así se guardan los intentos fallidos."""
    user = await users.get_by_email(command.email)
    code = await users.latest_code(user.id, PASSWORD_RESET) if user and user.is_active else None
    if code is None or not code.usable(datetime.now(UTC), MAX_CODE_ATTEMPTS):
        raise UnprocessableError(INVALID_CODE)
    if not same_secret(command.code, code.code_hash):
        await users.count_code_attempt(code.id)
        left = MAX_CODE_ATTEMPTS - code.attempts - 1
        raise UnprocessableError(f"Código incorrecto. Te quedan {left} intentos." if left else INVALID_CODE)
    await users.use_code(code.id)
    await users.set_password(user.id, await asyncio.to_thread(hash_password, command.new_password))
    _failed_logins.pop(user.email.lower(), None)  # si estaba bloqueado por intentos, ya puede entrar
    return user
