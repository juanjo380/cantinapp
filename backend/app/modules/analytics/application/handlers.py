"""Handlers de análisis histórico (RF-10, RF-11)."""
from app.core.exceptions import UnprocessableError
from app.modules.analytics.application.queries import ProductRankingQuery, SalesSeriesQuery
from datetime import timedelta

from app.modules.analytics.domain.entities import PERIOD_UNITS, abc_classify
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
        location_id=query.location_id,
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
        location_id=query.location_id,
    )


_ALL_PRODUCTS = 500  # shortcut: tope de productos en la clasificación; paginar si un negocio tiene más


async def classification(analytics: AnalyticsRepository, business_id, date_from, date_to, location_id=None):
    if date_from > date_to:
        raise UnprocessableError("date_from no puede ser mayor que date_to")
    length = (date_to - date_from).days + 1
    current = await analytics.product_ranking(
        business_id,
        order="top",
        limit=_ALL_PRODUCTS,
        date_from=date_from,
        date_to=date_to,
        location_id=location_id,
    )
    previous = await analytics.product_ranking(
        business_id,
        order="top",
        limit=_ALL_PRODUCTS,
        date_from=date_from - timedelta(days=length),
        date_to=date_from - timedelta(days=1),
        location_id=location_id,
    )
    return abc_classify(current, previous)
