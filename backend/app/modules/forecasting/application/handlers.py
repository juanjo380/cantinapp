"""Handler de predicción. Cumple RNF-04: exige al menos `min_history_days` de
historial; si no, responde 422."""
from datetime import date, timedelta

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.analytics.domain.repository import AnalyticsRepository
from app.modules.forecasting.application.commands import RunForecastCommand
from app.modules.forecasting.domain.accuracy import AccuracySummary, evaluate
from app.modules.forecasting.domain.entities import ModelType
from app.modules.forecasting.domain.models import dense_series, forecast
from app.modules.forecasting.domain.repository import ForecastRepository
from app.modules.products.domain.repository import ProductRepository

_MAX_HISTORY_WINDOW = 365
_ACCURACY_CANDIDATES = 60  # predicciones cumplidas a revisar; tras quitar recálculos quedan hasta 20


async def forecast_accuracy(
    analytics: AnalyticsRepository,
    forecasts: ForecastRepository,
    products: ProductRepository,
    business_id,
    product_id,
) -> AccuracySummary:
    if await products.get(business_id, product_id) is None:
        raise NotFoundError("Producto no encontrado")
    today = date.today()
    finished = await forecasts.finished(business_id, product_id, before=today, limit=_ACCURACY_CANDIDATES)
    if not finished:
        return evaluate([], {}, today)
    oldest = min(f.forecast_start for f in finished)
    days = min((today - oldest).days + 1, _MAX_HISTORY_WINDOW)
    actual = dict(await analytics.daily_series(business_id, product_id, days=days))
    return evaluate(finished, actual, today)


async def run_forecast(
    analytics: AnalyticsRepository,
    forecasts: ForecastRepository,
    products: ProductRepository,
    command: RunForecastCommand,
):
    settings = get_settings()
    product = await products.get(command.business_id, command.product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")

    model = command.model if command.model in {m.value for m in ModelType} else ModelType.AUTO.value
    forecast_days = command.forecast_days or settings.default_forecast_days

    first = await analytics.first_sale_date(command.business_id, command.product_id)
    today = date.today()
    history_days = (today - first).days + 1 if first else 0
    if first is None or history_days < settings.min_history_days:
        raise UnprocessableError(
            f"Datos insuficientes: se requieren al menos {settings.min_history_days} días de historial"
        )

    window = min(history_days, _MAX_HISTORY_WINDOW)
    rows = await analytics.daily_series(command.business_id, command.product_id, days=window)
    start = today - timedelta(days=window - 1)
    daily = dense_series({day: units for day, units in rows}, start, today)

    result = forecast(daily, forecast_days, model, start=today + timedelta(days=1))
    return await forecasts.add(
        business_id=command.business_id,
        product_id=command.product_id,
        model_type=result.model_type,
        requested_model=model,
        history_days=history_days,
        forecast_days=forecast_days,
        forecast_start=today + timedelta(days=1),
        predicted_demand=round(result.total, 2),
        confidence=result.confidence,
        backtest_wape=result.wape,
        backtest_mae=result.mae,
        daily_prediction=result.daily,
        created_by=command.created_by,
    )
