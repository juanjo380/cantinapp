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
from app.modules.recommendations.domain.events import (
    BASELINE_DAYS,
    event_extra_units,
    event_lift,
    order_by,
    past_occurrences,
    upcoming_events,
)
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


SEASON_HORIZON_DAYS = 120  # se avisa con tiempo: San Valentín aparece desde mediados de octubre
_SEASON_MAX_PRODUCTS = 10


async def seasonal_plan(analytics: AnalyticsRepository, inventory: InventoryRepository, business_id, today=None):
    """Próximas fechas comerciales y los productos que, en años anteriores, se dispararon alrededor de ellas."""
    today = today or date.today()
    events = upcoming_events(today, SEASON_HORIZON_DAYS)
    first = await analytics.first_sale_date(business_id)
    if not events or first is None:
        return []
    history: dict = defaultdict(dict)
    days = min((today - first).days + 1, 3 * _MAX_HISTORY_WINDOW)
    for product_id, day, units in await analytics.business_daily_series(business_id, days=days):
        history[product_id][day] = units
    # shortcut: hasta 200 productos (igual que el plan de compra); paginar si un negocio tiene más.
    items, _ = await inventory.list(business_id, limit=200)

    result = []
    for key, name, event_day in events:
        occurrences = past_occurrences(key, before=today, since=first)
        if not occurrences:
            continue
        found = []
        for item in items:
            daily = history.get(item.product_id, {})
            lift = event_lift(daily, occurrences)
            if lift is None:
                continue
            recent = sum(daily.get(today - timedelta(days=i), 0) for i in range(1, BASELINE_DAYS + 1)) / BASELINE_DAYS
            found.append(
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "lift": lift.lift,
                    "usual_daily": round(recent, 2),
                    "past_window_units": lift.window_units,
                    "years": lift.years,
                    "extra_units": event_extra_units(lift, recent),
                    "current_stock": item.stock_quantity,
                    "order_by": max(today, order_by(event_day, item.lead_time_days)),
                }
            )
        if found:
            found.sort(key=lambda f: -f["lift"])
            result.append(
                {"key": key, "name": name, "date": event_day, "days_until": (event_day - today).days,
                 "items": found[:_SEASON_MAX_PRODUCTS]}
            )
    return result
