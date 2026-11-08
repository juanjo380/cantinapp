"""Persistencia de los datos de ejemplo: productos con is_demo y ventas con source = 'DEMO'."""
from uuid import UUID

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sales.infrastructure.models import SaleRecord

# Orden por las FK: alertas -> recomendaciones -> predicciones; ventas antes que movimientos
# (borrar una venta que descontó stock inserta un movimiento de reversión).
_DELETE_STEPS = (
    "DELETE FROM alerts WHERE business_id = :bid AND product_id = ANY(:ids)",
    "DELETE FROM recommendations WHERE business_id = :bid AND product_id = ANY(:ids)",
    "DELETE FROM forecasts WHERE business_id = :bid AND product_id = ANY(:ids)",
    "DELETE FROM product_cooccurrences WHERE business_id = :bid "
    "AND (product_id = ANY(:ids) OR related_product_id = ANY(:ids))",
    "DELETE FROM sales WHERE business_id = :bid AND product_id = ANY(:ids)",
    "DELETE FROM inventory_movements WHERE business_id = :bid AND product_id = ANY(:ids)",
    "DELETE FROM products WHERE business_id = :bid AND id = ANY(:ids)",
)


class SqlDemoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def status(self, business_id: UUID) -> tuple[int, int, int]:
        """(productos de ejemplo, ventas de ejemplo, ventas en total)."""
        row = (
            await self.session.execute(
                text(
                    "SELECT (SELECT count(*) FROM products WHERE business_id = :bid AND is_demo),"
                    " (SELECT count(*) FROM sales WHERE business_id = :bid AND source = 'DEMO'),"
                    " (SELECT count(*) FROM sales WHERE business_id = :bid)"
                ),
                {"bid": business_id},
            )
        ).one()
        return row[0], row[1], row[2]

    async def mark_demo(self, business_id: UUID, product_ids: list[UUID]) -> None:
        await self.session.execute(
            text("UPDATE products SET is_demo = true WHERE business_id = :bid AND id = ANY(:ids)"),
            {"bid": business_id, "ids": product_ids},
        )

    async def insert_sales(self, rows: list[dict]) -> None:
        await self.session.execute(insert(SaleRecord), rows)  # executemany: ~1000 filas en una ida

    async def delete_all(self, business_id: UUID) -> int:
        ids = list(
            (
                await self.session.execute(
                    text("SELECT id FROM products WHERE business_id = :bid AND is_demo"), {"bid": business_id}
                )
            ).scalars()
        )
        if ids:
            for statement in _DELETE_STEPS:
                await self.session.execute(text(statement), {"bid": business_id, "ids": ids})
        return len(ids)
