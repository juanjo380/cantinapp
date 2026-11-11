"""Fachada de aplicación de productos."""
from app.modules.products.application import handlers
from app.modules.products.application.commands import (
    CreateProductCommand,
    ImportProductsCommand,
    UpdateProductCommand,
)
from app.modules.products.application.queries import GetProductQuery, ListProductsQuery
from app.modules.products.infrastructure.repository import SqlProductRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class ProductsFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.products = SqlProductRepository(uow.session)

    async def create(self, command: CreateProductCommand):
        product = await handlers.create_product(self.products, command)
        await self.uow.commit()
        return product

    async def import_csv(self, command: ImportProductsCommand):
        summary = await handlers.import_products(self.products, self.uow.session, command)
        await self.uow.commit()
        return summary

    async def update(self, command: UpdateProductCommand):
        product = await handlers.update_product(self.products, command)
        await self.uow.commit()
        return product

    async def deactivate(self, business_id, product_id) -> None:
        await handlers.deactivate_product(self.products, business_id, product_id)
        await self.uow.commit()

    async def composites(self, business_id):
        return await self.products.list_composites(business_id)

    async def set_recipe(self, business_id, product_id, items: dict) -> None:
        await handlers.set_recipe(self.products, business_id, product_id, items)
        await self.uow.commit()

    async def get(self, query: GetProductQuery):
        return await handlers.get_product(self.products, query)

    async def list(self, query: ListProductsQuery):
        return await handlers.list_products(self.products, query)
