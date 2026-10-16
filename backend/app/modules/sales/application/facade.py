"""Fachada de aplicación de ventas."""
from uuid import UUID

from app.modules.products.infrastructure.repository import SqlProductRepository
from app.modules.sales.application import handlers
from app.modules.sales.application.commands import CreateSaleCommand, ImportSalesCommand
from app.modules.sales.infrastructure.repository import SqlSaleRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class SalesFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.sales = SqlSaleRepository(uow.session)
        self.products = SqlProductRepository(uow.session)

    async def register(self, command: CreateSaleCommand):
        sale = await handlers.register_sale(self.sales, self.products, command)
        await self.uow.commit()
        return sale

    async def import_csv(self, command: ImportSalesCommand):
        summary = await handlers.import_sales(self.sales, self.products, self.uow.session, command)
        await self.uow.commit()
        return summary

    async def list(self, business_id: UUID, **filters):
        return await handlers.list_sales(self.sales, business_id, **filters)
