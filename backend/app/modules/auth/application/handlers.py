"""Handlers de los casos de uso de autenticación."""
import asyncio
import time
from functools import cache

from app.core.exceptions import ConflictError, TooManyRequestsError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.modules.auth.application.commands import LoginCommand, RegisterCommand
from app.modules.auth.domain.entities import Business, User
from app.modules.auth.domain.repository import BusinessRepository, UserRepository

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
    users: UserRepository, businesses: BusinessRepository, command: RegisterCommand
) -> tuple[User, Business]:
    """RF-01: crea negocio + usuario admin con email único."""
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
