"""Endpoints de ventas (RF-06, RF-07, RF-08)."""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.modules.sales.api.schemas import ImportOut, SaleCreate, SaleListOut, SaleOut
from app.modules.sales.application.commands import CreateSaleCommand, ImportSalesCommand
from app.modules.sales.application.facade import SalesFacade
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.post("", response_model=SaleOut, status_code=201)
async def create_sale(
    body: SaleCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    sale = await SalesFacade(uow).register(
        CreateSaleCommand(
            business_id=user.business_id,
            product_id=body.product_id,
            sale_date=body.sale_date,
            quantity=body.quantity,
            unit_price=body.unit_price,
            created_by=user.user_id,
        )
    )
    return SaleOut(**sale.__dict__)


@router.post("/import", response_model=ImportOut, status_code=201)
async def import_sales(
    file: UploadFile = File(...),
    affects_inventory: bool = Query(False, description="Si es true descuenta del stock actual"),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    raw = await file.read()
    content = raw.decode("utf-8-sig", errors="replace")
    summary = await SalesFacade(uow).import_csv(
        ImportSalesCommand(
            business_id=user.business_id,
            file_name=file.filename or "ventas.csv",
            content=content,
            affects_inventory=affects_inventory,
            created_by=user.user_id,
        )
    )
    return ImportOut(**summary.__dict__)


@router.get("", response_model=SaleListOut)
async def list_sales(
    product_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    items, total = await SalesFacade(uow).list(
        user.business_id,
        product_id=product_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return SaleListOut(items=[SaleOut(**item) for item in items], total=total, limit=limit, offset=offset)
