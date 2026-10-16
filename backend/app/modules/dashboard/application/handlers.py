"""Handler del dashboard (RF-14 / HU08). Agrega KPIs de varios módulos."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.application.queries import DashboardQuery


class DashboardHandlers:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, query: DashboardQuery) -> dict:
        business_id = query.business_id
        params = {"business_id": business_id}

        totals = (
            await self.session.execute(
                text(
                    "SELECT COUNT(*) FILTER (WHERE is_active) AS total_products, "
                    "COALESCE(SUM(stock_quantity) FILTER (WHERE is_active), 0) AS total_stock, "
                    "COALESCE(SUM(stock_quantity * price) FILTER (WHERE is_active), 0) AS inventory_value "
                    "FROM products WHERE business_id = :business_id"
                ),
                params,
            )
        ).mappings().one()

        period = (
            await self.session.execute(
                text(
                    "SELECT COALESCE(SUM(quantity), 0)::int AS units, COALESCE(SUM(total_amount), 0) AS revenue "
                    "FROM sales WHERE business_id = :business_id "
                    "AND date_trunc('month', sale_date) = date_trunc('month', CURRENT_DATE)"
                ),
                params,
            )
        ).mappings().one()

        low_stock = (
            await self.session.execute(
                text(
                    "SELECT product_id, name, stock_quantity, min_stock, status FROM v_inventory "
                    "WHERE business_id = :business_id AND status <> 'NORMAL' ORDER BY status, name LIMIT 50"
                ),
                params,
            )
        ).mappings().all()

        trend = (
            await self.session.execute(
                text(
                    "SELECT sale_date AS date, SUM(quantity)::int AS units FROM sales "
                    "WHERE business_id = :business_id AND sale_date >= CURRENT_DATE - CAST(:days AS int) "
                    "GROUP BY sale_date ORDER BY sale_date"
                ),
                {**params, "days": query.trend_days},
            )
        ).mappings().all()

        return {
            "total_products": totals["total_products"],
            "total_stock": totals["total_stock"],
            "inventory_value": totals["inventory_value"],
            "current_period": {"units_sold": period["units"], "revenue": period["revenue"]},
            "low_stock_products": [dict(row) for row in low_stock],
            "trend": [dict(row) for row in trend],
        }
