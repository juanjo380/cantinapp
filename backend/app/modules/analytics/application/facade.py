"""Fachada de aplicación de análisis."""
from app.modules.analytics.application import handlers
from app.modules.analytics.application.queries import ProductRankingQuery, SalesSeriesQuery
from app.modules.analytics.infrastructure.repository import SqlAnalyticsRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class AnalyticsFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.analytics = SqlAnalyticsRepository(uow.session)

    async def sales_series(self, query: SalesSeriesQuery):
        return await handlers.sales_series(self.analytics, query)

    async def product_ranking(self, query: ProductRankingQuery):
        return await handlers.product_ranking(self.analytics, query)
