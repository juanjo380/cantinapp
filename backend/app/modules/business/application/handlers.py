"""Reglas del negocio: quién puede editar el perfil, las sedes y el equipo.
Dueño y admin administran; el miembro solo consulta (y puede salirse). Al dueño no se le toca."""
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.modules.business.application.commands import (
    AddMemberCommand,
    ChangeRoleCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.business.domain.entities import BusinessProfile, Location, Member
from app.modules.business.domain.repository import BusinessProfileRepository
from app.shared.api.dependencies import CurrentUser


def _require_admin(actor: CurrentUser) -> None:
    if not actor.is_admin:
        raise ForbiddenError("Solo el dueño o un administrador del negocio puede hacer esto")


async def update_business(repo: BusinessProfileRepository, command: UpdateBusinessCommand) -> BusinessProfile:
    _require_admin(command.actor)
    return await repo.update(command.actor.business_id, command.changes)


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


async def add_member(repo: BusinessProfileRepository, command: AddMemberCommand) -> Member:
    _require_admin(command.actor)
    business_id = command.actor.business_id
    user_id = await repo.find_user_id(command.email)
    if user_id is None:
        raise NotFoundError(
            "No hay una cuenta con ese correo. Pídele que se registre en CantinAPP y vuelve a intentarlo"
        )
    if await repo.get_member(business_id, user_id) is not None:
        raise ConflictError("Esa persona ya pertenece al negocio")
    await repo.add_member(business_id, user_id, command.role)
    return await repo.get_member(business_id, user_id)


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
