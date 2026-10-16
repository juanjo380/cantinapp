"""Handlers de análisis histórico (RF-10, RF-11)."""
from app.core.exceptions import UnprocessableError
from app.modules.analytics.application.queries import ProductRankingQuery, SalesSeriesQuery
from app.modules.analytics.domain.entities import PERIOD_UNITS
from app.modules.analytics.domain.repository import AnalyticsRepository


async def sales_series(analytics: AnalyticsRepository, query: SalesSeriesQuery):
    if query.period not in PERIOD_UNITS:
        raise UnprocessableError("period debe ser daily, weekly, monthly o yearly")
    if query.date_from > query.date_to:
        raise UnprocessableError("date_from no puede ser mayor que date_to")
    return await analytics.sales_series(
        query.business_id,
        period=query.period,
        date_from=query.date_from,
        date_to=query.date_to,
        product_id=query.product_id,
    )


async def product_ranking(analytics: AnalyticsRepository, query: ProductRankingQuery):
    if query.order not in ("top", "bottom"):
        raise UnprocessableError("order debe ser top o bottom")
    return await analytics.product_ranking(
        query.business_id,
        order=query.order,
        limit=query.limit,
        date_from=query.date_from,
        date_to=query.date_to,
    )
