"""Fachada de aplicación del negocio."""
from uuid import UUID

from app.core.config import get_settings
from app.core.mailer import invitation_email, send_email
from app.modules.business.application import handlers
from app.modules.business.application.commands import (
    AcceptInvitationCommand,
    ChangeRoleCommand,
    InviteMemberCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.business.domain.entities import Invitation
from app.modules.business.infrastructure.repository import SqlBusinessProfileRepository
from app.shared.api.dependencies import CurrentUser
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

_ROLE_NAMES = {"ADMIN": "administrador", "MEMBER": "miembro"}


class BusinessFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.repo = SqlBusinessProfileRepository(uow.session)

    async def _commit(self, result):
        await self.uow.commit()
        return result

    async def get(self, business_id: UUID):
        return await self.repo.get(business_id)

    async def update(self, command: UpdateBusinessCommand):
        return await self._commit(await handlers.update_business(self.repo, command))

    async def ml_data_sharing(self, business_id: UUID) -> bool:
        return await self.repo.ml_data_sharing(business_id)

    async def set_ml_data_sharing(self, actor: CurrentUser, granted: bool) -> bool:
        return await self._commit(await handlers.set_ml_data_sharing(self.repo, actor, granted))

    async def locations(self, business_id: UUID):
        return await self.repo.list_locations(business_id)

    async def save_location(self, command: SaveLocationCommand):
        return await self._commit(await handlers.save_location(self.repo, command))

    async def delete_location(self, actor: CurrentUser, location_id: UUID) -> None:
        await self._commit(await handlers.delete_location(self.repo, actor, location_id))

    async def members(self, business_id: UUID):
        return await self.repo.list_members(business_id)

    async def invite(self, command: InviteMemberCommand) -> tuple[Invitation, str]:
        """Devuelve la invitación y el código de seguridad (solo se muestra esta vez)."""
        invitation, token, code = await handlers.invite_member(self.repo, command)
        link = f"{get_settings().frontend_url.rstrip('/')}/invitacion?token={token}"
        inviter = command.actor.full_name or command.actor.email
        # Se envía antes del commit: si el correo falla, la invitación no queda creada.
        await send_email(
            invitation.email,
            *invitation_email(
                invitation.business_name, _ROLE_NAMES[invitation.role], inviter, link, handlers.INVITATION_HOURS
            ),
        )
        await self.uow.commit()
        return invitation, code

    async def invitations(self, actor: CurrentUser) -> list[Invitation]:
        return await handlers.list_invitations(self.repo, actor)

    async def revoke_invitation(self, actor: CurrentUser, invitation_id: UUID) -> None:
        await self._commit(await handlers.revoke_invitation(self.repo, actor, invitation_id))

    async def invitation(self, email: str, token: str) -> Invitation:
        return await handlers.find_invitation(self.repo, email, token)

    async def accept_invitation(self, command: AcceptInvitationCommand) -> UUID:
        try:
            return await handlers.accept_invitation(self.repo, command)
        finally:
            await self.uow.commit()  # también guarda el intento con código incorrecto

    async def change_role(self, command: ChangeRoleCommand):
        return await self._commit(await handlers.change_role(self.repo, command))

    async def remove_member(self, command: RemoveMemberCommand) -> None:
        await self._commit(await handlers.remove_member(self.repo, command))
