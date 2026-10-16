"""Fachada de aplicación de predicción."""
from app.modules.analytics.infrastructure.repository import SqlAnalyticsRepository
from app.modules.forecasting.application.commands import RunForecastCommand
from app.modules.forecasting.application.handlers import run_forecast
from app.modules.forecasting.infrastructure.repository import SqlForecastRepository
from app.modules.products.infrastructure.repository import SqlProductRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class ForecastingFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.analytics = SqlAnalyticsRepository(uow.session)
        self.forecasts = SqlForecastRepository(uow.session)
        self.products = SqlProductRepository(uow.session)

    async def run(self, command: RunForecastCommand):
        result = await run_forecast(self.analytics, self.forecasts, self.products, command)
        await self.uow.commit()
        return result

    async def latest(self, business_id, product_id):
        return await self.forecasts.latest(business_id, product_id)

    async def list(self, business_id, product_id, limit=20):
        return await self.forecasts.list(business_id, product_id, limit=limit)
