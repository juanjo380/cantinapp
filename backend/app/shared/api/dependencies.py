"""Autenticación por request: valida el JWT y expone el usuario y su negocio
(RF-02, RNF-02). El `business_id` viene del usuario, nunca del cliente."""
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.shared.infrastructure.database import get_db

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    business_id: UUID
    email: str
    full_name: str | None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError("Falta el token de autenticación")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc

    row = (
        await session.execute(
            text(
                "SELECT id, business_id, email, full_name "
                "FROM users WHERE id = CAST(:id AS uuid) AND is_active"
            ),
            {"id": payload["sub"]},
        )
    ).mappings().first()
    if row is None:
        raise UnauthorizedError("Usuario no válido")
    return CurrentUser(
        user_id=row["id"], business_id=row["business_id"], email=row["email"], full_name=row["full_name"]
    )
