"""Fachada de aplicación de recomendación. Si no hay predicción reciente, la
genera antes de recomendar."""
from uuid import UUID

from app.modules.analytics.infrastructure.repository import SqlAnalyticsRepository
from app.modules.forecasting.application.commands import RunForecastCommand
from app.modules.forecasting.application.facade import ForecastingFacade
from app.modules.inventory.infrastructure.repository import SqlInventoryRepository
from app.modules.products.infrastructure.repository import SqlProductRepository
from app.modules.recommendations.application.commands import (
    CreateRecommendationCommand,
    RecomputeCoOccurrenceCommand,
)
from app.modules.recommendations.application.handlers import (
    create_recommendation,
    ensure_history,
    get_cooccurrence,
    recompute_cooccurrence,
)
from app.modules.recommendations.infrastructure.repository import (
    SqlCoOccurrenceRepository,
    SqlRecommendationRepository,
)
from app.shared.infrastructure.database import SessionFactory
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class RecommendationsFacade:
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow
        self.recommendations = SqlRecommendationRepository(uow.session)
        self.inventory = SqlInventoryRepository(uow.session)
        self.products = SqlProductRepository(uow.session)
        self.forecasting = ForecastingFacade(uow)
        self.analytics = SqlAnalyticsRepository(uow.session)
        self.cooccurrences = SqlCoOccurrenceRepository(uow.session)

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

    async def ensure_cooccurrence_history(self, business_id):
        await ensure_history(self.analytics, business_id)

    async def recompute_cooccurrence(self, command: RecomputeCoOccurrenceCommand) -> int:
        count = await recompute_cooccurrence(self.analytics, self.cooccurrences, command)
        await self.uow.commit()
        return count

    async def cooccurrence(self, business_id, product_id):
        return await get_cooccurrence(self.analytics, self.products, self.cooccurrences, business_id, product_id)


async def run_cooccurrence_job(business_id: UUID) -> int:
    """Recalcula fuera del request (BackgroundTasks o cron) con su propia sesión."""
    async with SessionFactory() as session:
        facade = RecommendationsFacade(SqlAlchemyUnitOfWork(session))
        return await facade.recompute_cooccurrence(RecomputeCoOccurrenceCommand(business_id=business_id))
