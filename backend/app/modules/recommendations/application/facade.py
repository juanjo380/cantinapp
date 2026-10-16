"""Fachada de aplicación de recomendación. Si no hay predicción reciente, la
genera antes de recomendar."""
from app.modules.forecasting.application.commands import RunForecastCommand
from app.modules.forecasting.application.facade import ForecastingFacade
from app.modules.inventory.infrastructure.repository import SqlInventoryRepository
from app.modules.products.infrastructure.repository import SqlProductRepository
from app.modules.recommendations.application.commands import CreateRecommendationCommand
from app.modules.recommendations.application.handlers import create_recommendation
from app.modules.recommendations.infrastructure.repository import SqlRecommendationRepository
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class RecommendationsFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.recommendations = SqlRecommendationRepository(uow.session)
        self.inventory = SqlInventoryRepository(uow.session)
        self.products = SqlProductRepository(uow.session)
        self.forecasting = ForecastingFacade(uow)

    async def create(self, command: CreateRecommendationCommand):
        forecast = await self.forecasting.latest(command.business_id, command.product_id)
        if forecast is None:
            forecast = await self.forecasting.run(
                RunForecastCommand(
                    business_id=command.business_id,
                    product_id=command.product_id,
                    forecast_days=command.forecast_days,
                    model=None,
                    created_by=command.created_by,
                )
            )
        recommendation = await create_recommendation(
            self.recommendations,
            self.inventory,
            self.products,
            command.business_id,
            command.product_id,
            forecast,
        )
        await self.uow.commit()
        return recommendation

    async def list(self, business_id, product_id, limit=20):
        return await self.recommendations.list(business_id, product_id, limit=limit)
