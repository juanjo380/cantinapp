"""Endpoints de predicción (RF-12 / HU06)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.forecasting.api.schemas import ForecastListOut, ForecastOut, ForecastRequest
from app.modules.forecasting.application.commands import RunForecastCommand
from app.modules.forecasting.application.facade import ForecastingFacade
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


def _forecast_out(forecast) -> ForecastOut:
    return ForecastOut(
        id=forecast.id,
        product_id=forecast.product_id,
        model_type=forecast.model_type,
        history_days=forecast.history_days,
        forecast_days=forecast.forecast_days,
        forecast_start=forecast.forecast_start,
        predicted_demand=forecast.predicted_demand,
        confidence=forecast.confidence,
        daily_prediction=forecast.daily_prediction,
    )


@router.post("", response_model=ForecastOut, status_code=201)
async def run_forecast(
    body: ForecastRequest,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    result = await ForecastingFacade(uow).run(
        RunForecastCommand(
            business_id=user.business_id,
            product_id=body.product_id,
            forecast_days=body.forecast_days,
            model=body.model,
            created_by=user.user_id,
        )
    )
    return _forecast_out(result)


@router.get("", response_model=ForecastListOut)
async def list_forecasts(
    product_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    items = await ForecastingFacade(uow).list(user.business_id, product_id, limit=limit)
    return ForecastListOut(items=[_forecast_out(item) for item in items])
