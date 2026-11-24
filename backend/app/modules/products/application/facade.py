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

    async def discount_suggestions(self, business_id, days: int):
        return await handlers.discount_suggestions(self.products, business_id, days)

    async def active_discounts(self, business_id):
        return await self.products.active_discounts(business_id)

    async def remove_discount(self, business_id, product_id):
        product = await handlers.remove_discount(self.products, business_id, product_id)
        await self.uow.commit()
        return product

    async def apply_discount(self, business_id, product_id, percent: int):
        product = await handlers.apply_discount(self.products, business_id, product_id, percent)
        await self.uow.commit()
        return product

    async def composites(self, business_id):
        return await self.products.list_composites(business_id)

    async def create_composite(self, command: CreateProductCommand, items: dict):
        product = await handlers.create_composite(self.products, command, items)
        await self.uow.commit()
        return product

    async def set_recipe(self, business_id, product_id, items: dict) -> None:
        await handlers.set_recipe(self.products, business_id, product_id, items)
        await self.uow.commit()

    async def get(self, query: GetProductQuery):
        return await handlers.get_product(self.products, query)

    async def list(self, query: ListProductsQuery):
        return await handlers.list_products(self.products, query)
