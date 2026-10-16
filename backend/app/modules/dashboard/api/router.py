"""Endpoint del dashboard (RF-14 / HU08)."""
from fastapi import APIRouter, Depends, Query

from app.modules.dashboard.api.schemas import DashboardOut
from app.modules.dashboard.application.handlers import DashboardHandlers
from app.modules.dashboard.application.queries import DashboardQuery
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
async def get_dashboard(
    trend_days: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    return await DashboardHandlers(uow.session).get(
        DashboardQuery(business_id=user.business_id, trend_days=trend_days)
    )
