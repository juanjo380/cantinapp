"""Endpoints de inventario (RF-09)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.inventory.api.schemas import (
    InventoryItemOut,
    InventoryListOut,
    MovementCreate,
    MovementListOut,
    MovementOut,
)
from app.modules.inventory.application.commands import RegisterMovementCommand
from app.modules.inventory.application.facade import InventoryFacade
from app.modules.inventory.application.queries import GetInventoryQuery, ListInventoryQuery, ListMovementsQuery
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=InventoryListOut)
async def list_inventory(
    status: str | None = Query(None, pattern="^(NORMAL|BAJO|AGOTADO)$"),
    category: str | None = None,
    search: str | None = None,
    sort: str = "name",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    page = await InventoryFacade(uow).list(
        ListInventoryQuery(
            business_id=user.business_id,
            status=status,
            category=category,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    )
    return InventoryListOut(
        items=[InventoryItemOut(**i.__dict__) for i in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("/movements", response_model=MovementOut, status_code=201)
async def register_movement(
    body: MovementCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    movement = await InventoryFacade(uow).register_movement(
        RegisterMovementCommand(
            business_id=user.business_id,
            product_id=body.product_id,
            movement_type=body.movement_type,
            quantity_change=body.quantity_change,
            notes=body.notes,
            created_by=user.user_id,
        )
    )
    return MovementOut(**movement.__dict__)


@router.get("/{product_id}", response_model=InventoryItemOut)
async def get_inventory(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    item = await InventoryFacade(uow).get(
        GetInventoryQuery(business_id=user.business_id, product_id=product_id)
    )
    return InventoryItemOut(**item.__dict__)


@router.get("/{product_id}/movements", response_model=MovementListOut)
async def list_movements(
    product_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    page = await InventoryFacade(uow).list_movements(
        ListMovementsQuery(business_id=user.business_id, product_id=product_id, limit=limit, offset=offset)
    )
    return MovementListOut(
        items=[MovementOut(**m.__dict__) for m in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )
