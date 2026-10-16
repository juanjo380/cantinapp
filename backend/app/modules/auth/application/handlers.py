"""Handlers de los casos de uso de autenticación."""
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.modules.auth.application.commands import LoginCommand, RegisterCommand
from app.modules.auth.domain.entities import Business, User
from app.modules.auth.domain.repository import BusinessRepository, UserRepository


async def register_user(
    users: UserRepository, businesses: BusinessRepository, command: RegisterCommand
) -> tuple[User, Business]:
    """RF-01: crea negocio + usuario admin con email único."""
    if await users.get_by_email(command.email) is not None:
        raise ConflictError("El email ya está registrado")
    business = await businesses.add(command.business_name.strip())
    user = await users.add(
        business_id=business.id,
        email=command.email.strip().lower(),
        password_hash=hash_password(command.password),
        full_name=command.full_name,
    )
    return user, business


async def authenticate(users: UserRepository, command: LoginCommand) -> User:
    """RF-02: valida credenciales."""
    stored = await users.get_password_hash(command.email)
    if stored is None or not verify_password(command.password, stored):
        raise UnauthorizedError("Credenciales inválidas")
    user = await users.get_by_email(command.email)
    if user is None or not user.is_active:
        raise UnauthorizedError("Usuario inactivo")
    return user
