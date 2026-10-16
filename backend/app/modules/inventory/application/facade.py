"""Fachada de aplicación de inventario."""
from app.modules.inventory.application import handlers
from app.modules.inventory.application.commands import RegisterMovementCommand
from app.modules.inventory.application.queries import GetInventoryQuery, ListInventoryQuery, ListMovementsQuery
from app.modules.inventory.infrastructure.repository import SqlInventoryRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class InventoryFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.inventory = SqlInventoryRepository(uow.session)

    async def register_movement(self, command: RegisterMovementCommand):
        movement = await handlers.register_movement(self.inventory, command)
        await self.uow.commit()
        return movement

    async def get(self, query: GetInventoryQuery):
        return await handlers.get_inventory(self.inventory, query)

    async def list(self, query: ListInventoryQuery):
        return await handlers.list_inventory(self.inventory, query)

    async def list_movements(self, query: ListMovementsQuery):
        return await handlers.list_movements(self.inventory, query)
