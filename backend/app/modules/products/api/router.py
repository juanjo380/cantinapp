"""Endpoints de productos (RF-04, RF-05)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import UnprocessableError
from app.modules.products.api.schemas import ProductCreate, ProductListOut, ProductOut, ProductUpdate
from app.modules.products.application.commands import CreateProductCommand, UpdateProductCommand
from app.modules.products.application.facade import ProductsFacade
from app.modules.products.application.queries import GetProductQuery, ListProductsQuery
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListOut)
async def list_products(
    search: str | None = None,
    category: str | None = None,
    active_only: bool = True,
    sort: str = "name",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    page = await ProductsFacade(uow).list(
        ListProductsQuery(
            business_id=user.business_id,
            search=search,
            category=category,
            active_only=active_only,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    )
    return ProductListOut(
        items=[ProductOut(**p.__dict__) for p in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(
    body: ProductCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    product = await ProductsFacade(uow).create(
        CreateProductCommand(business_id=user.business_id, **body.model_dump())
    )
    return ProductOut(**product.__dict__)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    product = await ProductsFacade(uow).get(
        GetProductQuery(business_id=user.business_id, product_id=product_id)
    )
    return ProductOut(**product.__dict__)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise UnprocessableError("No se enviaron campos para actualizar")
    product = await ProductsFacade(uow).update(
        UpdateProductCommand(business_id=user.business_id, product_id=product_id, changes=changes)
    )
    return ProductOut(**product.__dict__)


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    await ProductsFacade(uow).deactivate(user.business_id, product_id)
    return None
