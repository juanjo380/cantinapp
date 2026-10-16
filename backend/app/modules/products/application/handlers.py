"""Handlers de productos."""
from app.core.exceptions import NotFoundError
from app.modules.products.application.commands import CreateProductCommand, UpdateProductCommand
from app.modules.products.application.queries import GetProductQuery, ListProductsQuery
from app.modules.products.domain.entities import Product
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
