"""Fachada de aplicación de autenticación. Compone repositorios + handlers y
gestiona la transacción. Toda operación que cambia el negocio activo devuelve un token nuevo."""
from dataclasses import dataclass
from uuid import UUID

from app.core.mailer import password_changed_email, password_reset_email, send_email
from app.core.security import create_access_token
from app.modules.auth.application import handlers
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
from app.modules.auth.domain.entities import Session
from app.modules.auth.infrastructure.repository import (
    SqlBusinessRepository,
    SqlMembershipRepository,
    SqlUserRepository,
)
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class AuthResult:
    session: Session
    token: str


class AuthFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.users = SqlUserRepository(uow.session)
        self.businesses = SqlBusinessRepository(uow.session)
        self.memberships = SqlMembershipRepository(uow.session)

    async def register(self, command: RegisterCommand) -> AuthResult:
        user, business = await handlers.register_user(self.users, self.businesses, self.memberships, command)
        await self.uow.commit()
        return await self._issue(user.id, [business.id])

    async def login(self, command: LoginCommand) -> AuthResult:
        user = await handlers.authenticate(self.users, command)
        return self._result(await handlers.login_session(self.users, self.memberships, user))

    async def switch(self, command: SwitchBusinessCommand) -> AuthResult:
        session = await handlers.switch_business(self.users, self.memberships, command)
        await self.uow.commit()
        return self._result(session)

    async def create_business(self, command: CreateBusinessCommand) -> AuthResult:
        session = await handlers.create_business(self.users, self.businesses, self.memberships, command)
        await self.uow.commit()
        return self._result(session)

    async def session(self, user_id: UUID, business_id: UUID | None) -> Session:
        """Sesión del token actual: si ya no pertenece a ese negocio, sale sin negocio activo."""
        return await handlers.load_session(self.users, self.memberships, user_id, [business_id])

    async def update_profile(self, command: UpdateProfileCommand, business_id: UUID | None) -> Session:
        await handlers.update_profile(self.users, command)
        await self.uow.commit()
        return await self.session(command.user_id, business_id)

    async def change_password(self, command: ChangePasswordCommand, business_id: UUID | None) -> AuthResult:
        """Devuelve un token nuevo: el actual quedó invalidado junto con las demás sesiones."""
        await handlers.change_password(self.users, command)
        await self.uow.commit()
        await send_email(command.email, *password_changed_email(), quiet=True)
        return await self._issue(command.user_id, [business_id])

    async def request_password_reset(self, command: RequestPasswordResetCommand) -> None:
        code = await handlers.request_password_reset(self.users, command)
        if code:
            # Antes del commit: si el correo falla no queda un código que bloquee reintentar por 60 s.
            await send_email(command.email, *password_reset_email(code, handlers.RESET_CODE_MINUTES))
        await self.uow.commit()

    async def reset_password(self, command: ResetPasswordCommand) -> None:
        try:
            user = await handlers.reset_password(self.users, command)
        finally:
            await self.uow.commit()  # también guarda el intento fallido
        await send_email(user.email, *password_changed_email(), quiet=True)

    async def _issue(self, user_id: UUID, preferred: list[UUID | None]) -> AuthResult:
        return self._result(await handlers.load_session(self.users, self.memberships, user_id, preferred))

    def _result(self, session: Session) -> AuthResult:
        bid = str(session.business_id) if session.business_id else None
        return AuthResult(session=session, token=create_access_token(str(session.user.id), bid))
