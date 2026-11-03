"""Fachada de aplicación del negocio."""
from uuid import UUID

from app.modules.business.application import handlers
from app.modules.business.application.commands import (
    AddMemberCommand,
    ChangeRoleCommand,
    RemoveMemberCommand,
    SaveLocationCommand,
    UpdateBusinessCommand,
)
from app.modules.business.infrastructure.repository import SqlBusinessProfileRepository
from app.shared.api.dependencies import CurrentUser
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


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

    async def locations(self, business_id: UUID):
        return await self.repo.list_locations(business_id)

    async def save_location(self, command: SaveLocationCommand):
        return await self._commit(await handlers.save_location(self.repo, command))

    async def delete_location(self, actor: CurrentUser, location_id: UUID) -> None:
        await self._commit(await handlers.delete_location(self.repo, actor, location_id))

    async def members(self, business_id: UUID):
        return await self.repo.list_members(business_id)

    async def add_member(self, command: AddMemberCommand):
        return await self._commit(await handlers.add_member(self.repo, command))

    async def change_role(self, command: ChangeRoleCommand):
        return await self._commit(await handlers.change_role(self.repo, command))

    async def remove_member(self, command: RemoveMemberCommand) -> None:
        await self._commit(await handlers.remove_member(self.repo, command))
