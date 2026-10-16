"""Fachada de aplicación de autenticación. Compone repositorios + handlers y
gestiona la transacción."""
from dataclasses import dataclass

from app.core.security import create_access_token
from app.modules.auth.application.commands import LoginCommand, RegisterCommand
from app.modules.auth.application.handlers import authenticate, register_user
from app.modules.auth.domain.entities import Business, User
from app.modules.auth.infrastructure.repository import SqlBusinessRepository, SqlUserRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class AuthResult:
    user: User
    token: str
    business: Business | None = None


class AuthFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.users = SqlUserRepository(uow.session)
        self.businesses = SqlBusinessRepository(uow.session)

    async def register(self, command: RegisterCommand) -> AuthResult:
        user, business = await register_user(self.users, self.businesses, command)
        await self.uow.commit()
        return AuthResult(user=user, business=business, token=self._token(user))

    async def login(self, command: LoginCommand) -> AuthResult:
        user = await authenticate(self.users, command)
        return AuthResult(user=user, token=self._token(user))

    def _token(self, user: User) -> str:
        return create_access_token(str(user.id), str(user.business_id))
