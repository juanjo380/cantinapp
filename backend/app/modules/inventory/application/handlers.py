"""Handlers de inventario."""
from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.inventory.application.commands import RegisterMovementCommand
from app.modules.inventory.application.queries import GetInventoryQuery, ListInventoryQuery, ListMovementsQuery
from app.modules.inventory.domain.repository import InventoryRepository
from app.shared.domain.repository import Page


async def register_movement(inventory: InventoryRepository, command: RegisterMovementCommand):
    if command.movement_type not in ("PURCHASE", "ADJUSTMENT"):
        raise UnprocessableError("movement_type debe ser PURCHASE o ADJUSTMENT")
    if command.quantity_change == 0:
        raise UnprocessableError("quantity_change no puede ser cero")
    if command.movement_type == "PURCHASE" and command.quantity_change < 0:
        raise UnprocessableError("Una compra debe tener cantidad positiva")
    if await inventory.get(command.business_id, command.product_id) is None:
        raise NotFoundError("Producto no encontrado")
    return await inventory.add_movement(
        business_id=command.business_id,
        product_id=command.product_id,
        movement_type=command.movement_type,
        quantity_change=command.quantity_change,
        notes=command.notes,
        created_by=command.created_by,
    )


async def get_inventory(inventory: InventoryRepository, query: GetInventoryQuery):
    item = await inventory.get(query.business_id, query.product_id)
    if item is None:
        raise NotFoundError("Producto no encontrado")
    return item


async def list_inventory(inventory: InventoryRepository, query: ListInventoryQuery) -> Page:
    items, total = await inventory.list(
        query.business_id,
        status=query.status,
        category=query.category,
        search=query.search,
        sort=query.sort,
        limit=query.limit,
        offset=query.offset,
    )
    return Page(items=items, total=total, limit=query.limit, offset=query.offset)


async def list_movements(inventory: InventoryRepository, query: ListMovementsQuery) -> Page:
    items, total = await inventory.list_movements(
        query.business_id, query.product_id, limit=query.limit, offset=query.offset
    )
    return Page(items=items, total=total, limit=query.limit, offset=query.offset)
