"""Reglas del negocio: quién puede editar el perfil, las sedes y el equipo.
Dueño y admin administran; el miembro solo consulta (y puede salirse). Al dueño no se le toca."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from app.core.security import MAX_CODE_ATTEMPTS, hash_secret, new_code, new_link_token, same_secret
from app.modules.business.application.commands import (
    AcceptInvitationCommand,
    ChangeRoleCommand,
    InviteMemberCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.auth.application.handlers import LEGAL_VERSION
from app.modules.business.domain.entities import BusinessProfile, Invitation, Location, Member
from app.modules.business.domain.repository import BusinessProfileRepository
from app.shared.api.dependencies import CurrentUser

INVITATION_HOURS = 48


def _require_admin(actor: CurrentUser) -> None:
    if not actor.is_admin:
        raise ForbiddenError("Solo el dueño o un administrador del negocio puede hacer esto")


async def update_business(repo: BusinessProfileRepository, command: UpdateBusinessCommand) -> BusinessProfile:
    _require_admin(command.actor)
    return await repo.update(command.actor.business_id, command.changes)


async def set_ml_data_sharing(repo: BusinessProfileRepository, actor: CurrentUser, granted: bool) -> bool:
    """Autorización ML_ANONYMOUS del negocio: queda una fila nueva en user_consents (prueba, Ley 1581)."""
    _require_admin(actor)
    if await repo.ml_data_sharing(actor.business_id) != granted:
        await repo.set_ml_data_sharing(actor.business_id, actor.user_id, granted, LEGAL_VERSION)
    return granted


async def save_location(repo: BusinessProfileRepository, command: SaveLocationCommand) -> Location:
    _require_admin(command.actor)
    business_id = command.actor.business_id
    if command.location_id and await repo.get_location(business_id, command.location_id) is None:
        raise NotFoundError("Sede no encontrada")
    data = dict(command.data)
    if command.location_id is None and not await repo.list_locations(business_id):
        data["is_main"] = True  # la primera sede es la principal
    return await repo.save_location(business_id, command.location_id, data)


async def delete_location(repo: BusinessProfileRepository, actor: CurrentUser, location_id: UUID) -> None:
    _require_admin(actor)
    if await repo.get_location(actor.business_id, location_id) is None:
        raise NotFoundError("Sede no encontrada")
    await repo.delete_location(actor.business_id, location_id)


async def invite_member(repo: BusinessProfileRepository, command: InviteMemberCommand) -> tuple[Invitation, str, str]:
    """Crea la invitación y devuelve (invitación, token del enlace, código de seguridad).
    El enlace va al correo invitado; el código solo lo ve quien invita y lo dicta por otro medio:
    así aceptar exige el buzón de esa cuenta y hablar con quien invitó."""
    _require_admin(command.actor)
    business_id = command.actor.business_id
    user_id = await repo.find_user_id(command.email)
    if user_id is None:
        raise NotFoundError(
            "No hay una cuenta con ese correo. Pídele que se registre en CantinAPP y vuelve a intentarlo"
        )
    if await repo.get_member(business_id, user_id) is not None:
        raise ConflictError("Esa persona ya pertenece al negocio")
    token, code = new_link_token(), new_code()
    invitation = await repo.add_invitation(
        business_id=business_id,
        email=command.email,
        role=command.role,
        invited_by=command.actor.user_id,
        token_hash=hash_secret(token),
        code_hash=hash_secret(code),
        expires_at=datetime.now(UTC) + timedelta(hours=INVITATION_HOURS),
    )
    return invitation, token, code


async def list_invitations(repo: BusinessProfileRepository, actor: CurrentUser) -> list[Invitation]:
    _require_admin(actor)
    return await repo.list_invitations(actor.business_id)


async def revoke_invitation(repo: BusinessProfileRepository, actor: CurrentUser, invitation_id: UUID) -> None:
    _require_admin(actor)
    if not await repo.revoke_invitation(actor.business_id, invitation_id):
        raise NotFoundError("Invitación no encontrada")


async def find_invitation(repo: BusinessProfileRepository, email: str, token: str) -> Invitation:
    """La invitación del enlace, si sigue vigente y es para el correo de quien la abre."""
    invitation = await repo.find_invitation(hash_secret(token))
    if (
        invitation is None
        or invitation.expires_at <= datetime.now(UTC)
        or invitation.attempts >= MAX_CODE_ATTEMPTS
    ):
        raise NotFoundError("La invitación no existe, venció o ya se usó. Pide una nueva a quien te invitó")
    if invitation.email != email.lower():
        raise ForbiddenError("Esta invitación es para otro correo. Entra con la cuenta a la que llegó")
    return invitation


async def accept_invitation(repo: BusinessProfileRepository, command: AcceptInvitationCommand) -> UUID:
    """Devuelve el negocio al que entró. El que llama confirma la transacción aunque falle
    (guarda los intentos con código incorrecto)."""
    invitation = await find_invitation(repo, command.email, command.token)
    if not same_secret(command.code, invitation.code_hash):
        await repo.count_invitation_attempt(invitation.id)
        left = MAX_CODE_ATTEMPTS - invitation.attempts - 1
        raise UnprocessableError(
            f"Código incorrecto. Te quedan {left} intentos."
            if left
            else "Código incorrecto. La invitación quedó anulada; pide una nueva a quien te invitó."
        )
    if await repo.get_member(invitation.business_id, command.user_id) is None:
        await repo.add_member(invitation.business_id, command.user_id, invitation.role)
    await repo.accept_invitation(invitation.id)
    return invitation.business_id


async def _target(repo: BusinessProfileRepository, business_id: UUID, user_id: UUID) -> Member:
    member = await repo.get_member(business_id, user_id)
    if member is None:
        raise NotFoundError("Miembro no encontrado")
    if member.role == "OWNER":
        raise ForbiddenError("Al dueño del negocio no se le puede cambiar el rol ni quitar")
    return member


async def change_role(repo: BusinessProfileRepository, command: ChangeRoleCommand) -> Member:
    _require_admin(command.actor)
    await _target(repo, command.actor.business_id, command.user_id)
    await repo.set_role(command.actor.business_id, command.user_id, command.role)
    return await repo.get_member(command.actor.business_id, command.user_id)


async def remove_member(repo: BusinessProfileRepository, command: RemoveMemberCommand) -> None:
    if command.user_id != command.actor.user_id:  # salirse uno mismo no requiere ser admin
        _require_admin(command.actor)
    await _target(repo, command.actor.business_id, command.user_id)
    await repo.remove_member(command.actor.business_id, command.user_id)
