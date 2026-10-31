"""Handler de recomendación. Combina inventario + predicción (regla de
dependencia: Recomendación llama a Predicción e Inventario)."""
from collections import defaultdict
from datetime import date, timedelta

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.analytics.domain.repository import AnalyticsRepository
from app.modules.forecasting.domain.entities import Forecast
from app.modules.forecasting.domain.models import dense_series
from app.modules.inventory.domain.repository import InventoryRepository
from app.modules.products.domain.repository import ProductRepository
from app.modules.recommendations.application.commands import RecomputeCoOccurrenceCommand
from app.modules.recommendations.domain.cooccurrence import cooccurrence_scores
from app.modules.recommendations.domain.policy import build_recommendation
from app.modules.recommendations.domain.repository import CoOccurrenceRepository, RecommendationRepository


async def create_recommendation(
    recommendations: RecommendationRepository,
    inventory: InventoryRepository,
    products: ProductRepository,
    business_id,
    product_id,
    forecast: Forecast,
):
    if await products.get(business_id, product_id) is None:
        raise NotFoundError("Producto no encontrado")
    item = await inventory.get(business_id, product_id)
    if item is None:
        raise NotFoundError("Producto no encontrado en inventario")

    draft = build_recommendation(
        current_stock=item.stock_quantity,
        min_stock=item.min_stock,
        lead_time_days=item.lead_time_days,
        predicted_demand=float(forecast.predicted_demand),
        forecast_days=forecast.forecast_days,
    )
    return await recommendations.add(
        business_id=business_id, product_id=product_id, forecast_id=forecast.id, draft=draft
    )


_MAX_HISTORY_WINDOW = 365


async def ensure_history(analytics: AnalyticsRepository, business_id, product_id=None) -> int:
    """Días de historial (del negocio o del producto); 422 si no llega al mínimo (RNF-04)."""
    settings = get_settings()
    first = await analytics.first_sale_date(business_id, product_id)
    history_days = (date.today() - first).days + 1 if first else 0
    if history_days < settings.min_history_days:
        raise UnprocessableError(
            f"Datos insuficientes: se requieren al menos {settings.min_history_days} días de historial"
        )
    return history_days


async def recompute_cooccurrence(
    analytics: AnalyticsRepository,
    cooccurrences: CoOccurrenceRepository,
    command: RecomputeCoOccurrenceCommand,
) -> int:
    settings = get_settings()
    window = min(await ensure_history(analytics, command.business_id), _MAX_HISTORY_WINDOW)
    today = date.today()
    start = today - timedelta(days=window - 1)

    history: dict = defaultdict(dict)
    for product_id, day, units in await analytics.business_daily_series(command.business_id, days=window):
        history[product_id][day] = units
    pairs = cooccurrence_scores(
        {product_id: dense_series(days, start, today) for product_id, days in history.items()},
        window=settings.cooccurrence_window_days,
        sigma=settings.cooccurrence_sigma,
        max_lag=settings.cooccurrence_max_lag_days,
        min_hits=settings.cooccurrence_min_hits,
    )
    await cooccurrences.replace(command.business_id, pairs)
    return len(pairs)


async def get_cooccurrence(
    analytics: AnalyticsRepository,
    products: ProductRepository,
    cooccurrences: CoOccurrenceRepository,
    business_id,
    product_id,
):
    if await products.get(business_id, product_id) is None:
        raise NotFoundError("Producto no encontrado")
    await ensure_history(analytics, business_id, product_id)
    return await cooccurrences.list(business_id, product_id)
