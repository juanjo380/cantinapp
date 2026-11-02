"""Handlers de productos."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.products.application.commands import (
    CreateProductCommand,
    ImportProductsCommand,
    UpdateProductCommand,
)
from app.modules.products.application.csv_parser import parse_products_csv
from app.modules.products.application.queries import GetProductQuery, ListProductsQuery
from app.modules.products.domain.entities import Product, ProductImport
from app.modules.products.domain.repository import ProductRepository
from app.shared.domain.repository import Page


async def create_product(products: ProductRepository, command: CreateProductCommand) -> Product:
    return await products.add(
        business_id=command.business_id,
        name=command.name,
        category=command.category,
        supplier=command.supplier,
        price=command.price,
        quantity=command.quantity,
        min_stock=command.min_stock,
        lead_time_days=command.lead_time_days,
    )


async def import_products(
    products: ProductRepository, session: AsyncSession, command: ImportProductsCommand
) -> ProductImport:
    """Crea los productos válidos del CSV; las filas con error se reportan y no detienen la carga."""
    parsed, errors = parse_products_csv(command.content)
    total_rows = len(parsed) + len({e["row"] for e in errors if e["row"] > 0})
    imported = 0
    for row in parsed:
        if await products.get_by_name(command.business_id, row.name) is not None:
            errors.append({"row": row.row_number, "field": "name", "message": "Ya existe un producto activo con ese nombre"})
            continue
        try:
            async with session.begin_nested():  # una fila fallida no deshace las demás
                await products.add(
                    business_id=command.business_id,
                    name=row.name,
                    category=row.category,
                    supplier=row.supplier,
                    price=row.price,
                    quantity=row.quantity,
                    min_stock=row.min_stock,
                    lead_time_days=row.lead_time_days,
                )
            imported += 1
        except IntegrityError:
            errors.append({"row": row.row_number, "field": "name", "message": "No se pudo crear (nombre duplicado)"})

    return ProductImport(
        file_name=command.file_name,
        total_rows=total_rows,
        imported_rows=imported,
        error_rows=len({e["row"] for e in errors}),
        status="COMPLETED" if imported > 0 or not errors else "FAILED",
        errors=sorted(errors, key=lambda e: e["row"]),
    )


async def update_product(products: ProductRepository, command: UpdateProductCommand) -> Product:
    product = await _require(products, command.business_id, command.product_id)
    return await products.update(product, command.changes)


async def deactivate_product(products: ProductRepository, business_id, product_id) -> None:
    product = await _require(products, business_id, product_id)
    await products.deactivate(product)


async def get_product(products: ProductRepository, query: GetProductQuery) -> Product:
    return await _require(products, query.business_id, query.product_id)


async def list_products(products: ProductRepository, query: ListProductsQuery) -> Page[Product]:
    items, total = await products.list(
        query.business_id,
        search=query.search,
        category=query.category,
        active_only=query.active_only,
        sort=query.sort,
        limit=query.limit,
        offset=query.offset,
    )
    return Page(items=items, total=total, limit=query.limit, offset=query.offset)


async def _require(products: ProductRepository, business_id, product_id) -> Product:
    product = await products.get(business_id, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    return product
