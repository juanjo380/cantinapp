"""Autenticación por request: valida el JWT y expone el usuario y su negocio
(RF-02, RNF-02). El `business_id` viene del token y se verifica contra
`business_members` en cada request: nunca se acepta desde el cliente."""
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.shared.infrastructure.database import get_db

_bearer = HTTPBearer(auto_error=False)
ADMIN_ROLES = ("OWNER", "ADMIN")


@dataclass(frozen=True)
class CurrentAccount:
    """Usuario autenticado, tenga o no un negocio activo (perfil, cambio de negocio)."""

    user_id: UUID
    email: str
    full_name: str | None
    business_id: UUID | None  # negocio del token, sin verificar pertenencia


@dataclass(frozen=True)
class CurrentUser:
    """Usuario con pertenencia verificada al negocio activo: lo usan todos los módulos de negocio."""

    user_id: UUID
    business_id: UUID
    email: str
    full_name: str | None
    role: str = "MEMBER"
    location_id: UUID | None = None  # sede asignada; None = todas (el dueño siempre ve todas)

    def scoped_location(self, requested: UUID | None) -> UUID | None:
        """Sede cuyas ventas y métricas ve: la asignada manda; sin sede asignada, la pedida (None = todas)."""
        return self.location_id or requested

    @property
    def is_admin(self) -> bool:
        return self.role in ADMIN_ROLES

    @property
    def is_owner(self) -> bool:
        return self.role == "OWNER"


def _decode(credentials: HTTPAuthorizationCredentials | None) -> tuple[UUID, UUID | None, datetime]:
    if credentials is None:
        raise UnauthorizedError("Falta el token de autenticación")
    try:
        payload = decode_access_token(credentials.credentials)
        bid = payload.get("bid")
        # +1 s: `iat` va en segundos enteros y el token nuevo se emite justo después del cambio.
        issued = datetime.fromtimestamp(int(payload.get("iat", 0)) + 1, UTC)
        return UUID(payload["sub"]), UUID(bid) if bid else None, issued
    except ValueError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc


async def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> CurrentAccount:
    user_id, business_id, issued = _decode(credentials)
    # Cambiar la contraseña invalida los tokens emitidos antes (cierra las demás sesiones).
    row = (
        await session.execute(
            text(
                "SELECT id, email, full_name FROM users WHERE id = :id AND is_active"
                " AND (password_changed_at IS NULL OR password_changed_at < :issued)"
            ),
            {"id": user_id, "issued": issued},
        )
    ).mappings().first()
    if row is None:
        raise UnauthorizedError("Usuario no válido")
    return CurrentAccount(
        user_id=row["id"], email=row["email"], full_name=row["full_name"], business_id=business_id
    )


async def get_current_user(
    account: CurrentAccount = Depends(get_current_account),
    session: AsyncSession = Depends(get_db),
) -> CurrentUser:
    # 403 (no 401): la sesión sigue siendo válida, el cliente debe elegir otro negocio.
    if account.business_id is None:
        raise ForbiddenError("Elige o crea un negocio para continuar")
    member = (
        await session.execute(
            text("SELECT role, location_id FROM business_members WHERE business_id = :bid AND user_id = :uid"),
            {"bid": account.business_id, "uid": account.user_id},
        )
    ).mappings().first()
    if member is None:
        raise ForbiddenError("Ya no perteneces a este negocio. Elige otro para continuar")
    return CurrentUser(
        user_id=account.user_id,
        business_id=account.business_id,
        email=account.email,
        full_name=account.full_name,
        role=member["role"],
        location_id=None if member["role"] == "OWNER" else member["location_id"],
    )


async def get_admin_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise ForbiddenError("Solo el dueño o un administrador del negocio puede hacer esto")
    return user
