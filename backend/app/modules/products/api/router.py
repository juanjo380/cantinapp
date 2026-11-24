"""Endpoints de productos (RF-04, RF-05)."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.exceptions import UnprocessableError
from app.modules.products.api.schemas import (
    CompositeCreate,
    ActiveDiscountOut,
    CompositeOut,
    DiscountIn,
    DiscountSuggestionOut,
    DiscountSuggestionsOut,
    ProductCreate,
    ProductImportOut,
    ProductListOut,
    ProductOut,
    ProductUpdate,
    RecipeIn,
)
from app.modules.products.application.commands import (
    CreateProductCommand,
    ImportProductsCommand,
    UpdateProductCommand,
)
from app.modules.products.application.csv_parser import TEMPLATE
from app.modules.products.application.facade import ProductsFacade
from app.modules.products.application.queries import GetProductQuery, ListProductsQuery
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.api.uploads import csv_template_response, read_csv_upload
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/import/template")
async def import_template():
    """Público: es un archivo fijo de ejemplo, no contiene datos de ningún negocio."""
    return csv_template_response(TEMPLATE, "plantilla-productos.csv")


@router.get("", response_model=ProductListOut)
async def list_products(
    search: str | None = None,
    category: str | None = None,
    active_only: bool = True,
    composite: bool | None = None,
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
            composite=composite,
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


@router.post("/import", response_model=ProductImportOut, status_code=201)
async def import_products(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    content = await read_csv_upload(file)
    summary = await ProductsFacade(uow).import_csv(
        ImportProductsCommand(
            business_id=user.business_id, file_name=file.filename or "productos.csv", content=content
        )
    )
    return ProductImportOut(**summary.__dict__)


# Antes de /{product_id} para que «discounts» no se lea como id.
@router.get("/discounts", response_model=DiscountSuggestionsOut)
async def discount_suggestions(
    days: int = Query(30, ge=7, le=180),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    facade = ProductsFacade(uow)
    items = await facade.discount_suggestions(user.business_id, days)
    active = await facade.active_discounts(user.business_id)
    return DiscountSuggestionsOut(
        days=days,
        items=[DiscountSuggestionOut(**i.__dict__) for i in items],
        active=[ActiveDiscountOut(**a.__dict__) for a in active],
    )


@router.post("/{product_id}/discount", response_model=ProductOut)
async def apply_discount(
    product_id: UUID,
    body: DiscountIn,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    product = await ProductsFacade(uow).apply_discount(user.business_id, product_id, body.percent)
    return ProductOut(**product.__dict__)


@router.delete("/{product_id}/discount", response_model=ProductOut)
async def remove_discount(
    product_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    """Vuelve al precio de lista guardado al aplicar el descuento."""
    return ProductOut(**(await ProductsFacade(uow).remove_discount(user.business_id, product_id)).__dict__)


@router.get("/composites", response_model=list[CompositeOut])
async def list_composites(user: CurrentUser = Depends(get_current_user), uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    return await ProductsFacade(uow).composites(user.business_id)


@router.post("/composites", response_model=ProductOut, status_code=201)
async def create_composite(
    body: CompositeCreate,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    command = CreateProductCommand(
        business_id=user.business_id, name=body.name, category=body.category, price=body.price,
        quantity=0, min_stock=body.min_stock, lead_time_days=0,
    )
    items = {c.component_id: c.quantity for c in body.components}
    return ProductOut(**(await ProductsFacade(uow).create_composite(command, items)).__dict__)


@router.put("/{product_id}/components", status_code=204)
async def set_recipe(
    product_id: UUID,
    body: RecipeIn,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    items = {c.component_id: c.quantity for c in body.components}
    await ProductsFacade(uow).set_recipe(user.business_id, product_id, items)
    return None


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
