"""Cargar y borrar datos de ejemplo. Solo el dueño, y cargar solo en un negocio sin ventas:
así los datos de ejemplo nunca se mezclan con ventas reales sin que el dueño lo decida."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError
from app.modules.alerts.infrastructure.repository import SqlAlertRepository
from app.modules.demo.domain import generator
from app.modules.demo.infrastructure.repository import SqlDemoRepository
from app.modules.products.infrastructure.repository import SqlProductRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class DemoStatus:
    has_demo: bool
    can_load: bool
    demo_products: int
    demo_sales: int


class DemoFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.demo = SqlDemoRepository(uow.session)
        self.products = SqlProductRepository(uow.session)
        self.alerts = SqlAlertRepository(uow.session)

    async def status(self, business_id: UUID, role: str) -> DemoStatus:
        demo_products, demo_sales, all_sales = await self.demo.status(business_id)
        return DemoStatus(
            has_demo=demo_products > 0,
            can_load=role == "OWNER" and demo_products == 0 and all_sales == 0,
            demo_products=demo_products,
            demo_sales=demo_sales,
        )

    async def load(self, business_id: UUID, role: str, user_id: UUID) -> DemoStatus:
        _require_owner(role)
        demo_products, _, all_sales = await self.demo.status(business_id)
        if demo_products:
            raise ConflictError("Ya cargaste los datos de ejemplo en este negocio")
        if all_sales:
            raise ConflictError("Este negocio ya tiene ventas: los datos de ejemplo solo se cargan en uno vacío")

        catalog = generator.products()
        created = [
            await self.products.add(
                business_id=business_id,
                name=p.name,
                category=p.category,
                supplier=p.supplier,
                price=p.price,
                quantity=p.stock,
                min_stock=p.min_stock,
                lead_time_days=p.lead_time_days,
            )
            for p in catalog
        ]
        await self.demo.mark_demo(business_id, [p.id for p in created])
        await self.demo.insert_sales(
            [
                {
                    "business_id": business_id,
                    "product_id": created[s.product].id,
                    "sale_date": s.sale_date,
                    "quantity": s.quantity,
                    "unit_price": s.unit_price,
                    "source": "DEMO",
                    "affects_inventory": False,  # historial: el stock de ejemplo queda como se definió
                    "created_by": user_id,
                }
                for s in generator.sales(date.today())
            ]
        )
        await self.alerts.generate_pending(business_id)
        await self.uow.commit()
        return await self.status(business_id, role)

    async def clear(self, business_id: UUID, role: str) -> int:
        _require_owner(role)
        deleted = await self.demo.delete_all(business_id)
        await self.uow.commit()
        return deleted


def _require_owner(role: str) -> None:
    if role != "OWNER":
        raise ForbiddenError("Solo el dueño del negocio puede cargar o borrar los datos de ejemplo")
