"""Adaptador de lectura de análisis histórico (consultas agregadas sobre `sales`)."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.domain.entities import PERIOD_UNITS, ProductRanking, SalesSeriesPoint
from app.modules.analytics.domain.repository import AnalyticsRepository


# Patrón semanal agregado entre negocios que autorizaron ML_ANONYMOUS (la fila más reciente del
# negocio manda). Se excluyen ventas DEMO y el propio negocio. Días sin ventas cuentan como 0.
# Solo sale (¿mismo tipo de negocio que :exclude?, día, factor promedio, n.º de negocios): ningún id ni nombre.
_POOLED_WEEKDAY_SQL = """
WITH consent AS (
    SELECT DISTINCT ON (business_id) business_id, granted FROM user_consents
    WHERE document = 'ML_ANONYMOUS' ORDER BY business_id, created_at DESC
), daily AS (
    SELECT s.business_id, s.sale_date, SUM(s.quantity) AS units FROM sales s
    JOIN consent c ON c.business_id = s.business_id AND c.granted
    WHERE s.source <> 'DEMO' AND s.business_id <> :exclude
      AND s.sale_date BETWEEN CURRENT_DATE - CAST(:days AS int) AND CURRENT_DATE - 1
    GROUP BY 1, 2
), dense AS (
    SELECT g.business_id, g.day, COALESCE(d.units, 0) AS units
    FROM (SELECT business_id, generate_series(MIN(sale_date), CURRENT_DATE - 1, interval '1 day')::date AS day
          FROM daily GROUP BY business_id) g
    LEFT JOIN daily d ON d.business_id = g.business_id AND d.sale_date = g.day
), level AS (
    SELECT business_id, AVG(units) AS level FROM dense GROUP BY 1 HAVING COUNT(*) >= 28 AND AVG(units) > 0
), factors AS (
    SELECT d.business_id, EXTRACT(ISODOW FROM d.day)::int - 1 AS weekday, AVG(d.units) / l.level AS factor
    FROM dense d JOIN level l USING (business_id) GROUP BY d.business_id, 2, l.level
)
SELECT (NULLIF(lower(trim(b.business_type)), '') = (
            SELECT NULLIF(lower(trim(business_type)), '') FROM businesses WHERE id = :exclude
        )) IS TRUE AS same_type, f.weekday,
       AVG(f.factor)::float AS factor, COUNT(*)::int AS businesses
FROM factors f JOIN businesses b ON b.id = f.business_id
GROUP BY 1, 2
"""


class SqlAnalyticsRepository(AnalyticsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def sales_series(
        self,
        business_id: UUID,
        *,
        period: str,
        date_from: date,
        date_to: date,
        product_id: UUID | None = None,
        location_id: UUID | None = None,
    ) -> list[SalesSeriesPoint]:
        unit = PERIOD_UNITS.get(period, "day")
        condition = "AND product_id = :product_id" if product_id else ""
        if location_id:
            condition += " AND location_id = :location_id"
        rows = (
            await self.session.execute(
                text(
                    f"SELECT date_trunc('{unit}', sale_date)::date AS period, "
                    "COALESCE(SUM(quantity), 0)::int AS units, COALESCE(SUM(total_amount), 0) AS revenue "
                    "FROM sales WHERE business_id = :business_id "
                    f"AND sale_date BETWEEN :date_from AND :date_to {condition} "
                    "GROUP BY 1 ORDER BY 1"
                ),
                {
                    "business_id": business_id,
                    "date_from": date_from,
                    "date_to": date_to,
                    **({"product_id": product_id} if product_id else {}),
                    **({"location_id": location_id} if location_id else {}),
                },
            )
        ).mappings().all()
        return [SalesSeriesPoint(period=r["period"], units=r["units"], revenue=r["revenue"]) for r in rows]

    async def product_ranking(
        self,
        business_id: UUID,
        *,
        order: str,
        limit: int,
        date_from: date,
        date_to: date,
        location_id: UUID | None = None,
    ) -> list[ProductRanking]:
        direction = "ASC" if order == "bottom" else "DESC"
        condition = "AND s.location_id = :location_id" if location_id else ""
        rows = (
            await self.session.execute(
                text(
                    "SELECT s.product_id, p.name, SUM(s.quantity)::int AS units, "
                    "COALESCE(SUM(s.total_amount), 0) AS revenue "
                    "FROM sales s JOIN products p ON p.id = s.product_id AND p.business_id = s.business_id "
                    f"WHERE s.business_id = :business_id AND s.sale_date BETWEEN :date_from AND :date_to {condition} "
                    f"GROUP BY 1, 2 ORDER BY units {direction} LIMIT :limit"
                ),
                {
                    "business_id": business_id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "limit": limit,
                    **({"location_id": location_id} if location_id else {}),
                },
            )
        ).mappings().all()
        return [
            ProductRanking(product_id=r["product_id"], name=r["name"], units=r["units"], revenue=r["revenue"])
            for r in rows
        ]

    async def daily_series(self, business_id: UUID, product_id: UUID, *, days: int) -> list[tuple[date, int]]:
        rows = (
            await self.session.execute(
                text(
                    "SELECT sale_date, SUM(quantity)::int AS units FROM sales "
                    "WHERE business_id = :business_id AND product_id = :product_id "
                    "AND sale_date >= CURRENT_DATE - CAST(:days AS int) "
                    "GROUP BY sale_date ORDER BY sale_date"
                ),
                {"business_id": business_id, "product_id": product_id, "days": days},
            )
        ).all()
        return [(r[0], r[1]) for r in rows]

    async def business_daily_series(self, business_id: UUID, *, days: int) -> list[tuple[UUID, date, int]]:
        rows = (
            await self.session.execute(
                text(
                    "SELECT product_id, sale_date, units_sold::int FROM v_daily_sales "
                    "WHERE business_id = :business_id AND sale_date >= CURRENT_DATE - CAST(:days AS int)"
                ),
                {"business_id": business_id, "days": days},
            )
        ).all()
        return [(r[0], r[1], r[2]) for r in rows]

    async def first_sale_date(self, business_id: UUID, product_id: UUID | None = None) -> date | None:
        condition = "AND product_id = :product_id" if product_id else ""
        return (
            await self.session.execute(
                text(f"SELECT MIN(sale_date) FROM sales WHERE business_id = :business_id {condition}"),
                {"business_id": business_id, **({"product_id": product_id} if product_id else {})},
            )
        ).scalar_one_or_none()

    async def pooled_weekday_factors(
        self, *, exclude_business_id: UUID, days: int
    ) -> list[tuple[bool, int, float, int]]:
        rows = (
            await self.session.execute(text(_POOLED_WEEKDAY_SQL), {"exclude": exclude_business_id, "days": days})
        ).all()
        return [(r[0], r[1], r[2], r[3]) for r in rows]
