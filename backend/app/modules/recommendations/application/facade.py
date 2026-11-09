"""Fachada de aplicación de recomendación. Si no hay predicción reciente, la
genera antes de recomendar."""
from datetime import date, timedelta
from uuid import UUID

from app.core.exceptions import UnprocessableError

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
    seasonal_plan,
)
from app.modules.recommendations.domain.policy import build_recommendation, plan_order
from app.modules.recommendations.infrastructure.repository import (
    SqlCoOccurrenceRepository,
    SqlRecommendationRepository,
)
from app.shared.infrastructure.database import SessionFactory
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


PLAN_SIZE = 15


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

    async def plan(self, business_id, user_id) -> tuple[list[tuple], list[str]]:
        """Plan de compra de todo el inventario: [(producto, predicción, recomendación)] ordenado por
        urgencia, y los nombres de los productos que aún no tienen historial suficiente.
        La predicción de hoy se reutiliza; las recomendaciones no se guardan (el stock cambia)."""
        # Solo los 15 más vendidos del último mes: es lo que mueve la caja y limita las predicciones
        # por request. Lo que no se vendió en 30 días no entra (las alertas de stock sí lo cubren).
        today = date.today()
        ranking = await self.analytics.product_ranking(
            business_id, order="top", limit=PLAN_SIZE, date_from=today - timedelta(days=29), date_to=today
        )
        items = [item for r in ranking if (item := await self.inventory.get(business_id, r.product_id))]
        tomorrow = today + timedelta(days=1)
        plan, pending = [], []
        for item in items:
            forecast = await self.forecasting.latest(business_id, item.product_id)
            if forecast is None or forecast.forecast_start != tomorrow:
                try:
                    forecast = await self.forecasting.run(
                        RunForecastCommand(
                            business_id=business_id,
                            product_id=item.product_id,
                            forecast_days=None,
                            model=None,
                            created_by=user_id,
                        )
                    )
                except UnprocessableError:
                    pending.append(item.name)
                    continue
            draft = build_recommendation(
                current_stock=item.stock_quantity,
                min_stock=item.min_stock,
                lead_time_days=item.lead_time_days,
                predicted_demand=float(forecast.predicted_demand),
                forecast_days=forecast.forecast_days,
            )
            plan.append((item, forecast, draft))
        plan.sort(key=lambda entry: plan_order(entry[2]))
        return plan, pending

    async def seasonal(self, business_id):
        return await seasonal_plan(self.analytics, self.inventory, business_id)

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
