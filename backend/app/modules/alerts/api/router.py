"""Endpoints de alertas (RF-15 / HU09)."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.alerts.api.schemas import AlertListOut, AlertOut, GenerateAlertsOut
from app.modules.alerts.application.commands import GenerateAlertsCommand, ReviewAlertCommand
from app.modules.alerts.application.handlers import generate_alerts, list_alerts, review_alert
from app.modules.alerts.application.queries import ListAlertsQuery
from app.modules.alerts.infrastructure.repository import SqlAlertRepository
from app.shared.api.dependencies import CurrentUser, get_current_user
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, get_uow

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListOut)
async def get_alerts(
    status: str | None = Query(None, pattern="^(PENDING|REVIEWED|pending|reviewed)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    page = await list_alerts(
        SqlAlertRepository(uow.session),
        ListAlertsQuery(business_id=user.business_id, status=status, limit=limit, offset=offset),
    )
    return AlertListOut(
        items=[AlertOut(**a.__dict__) for a in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.post("/generate", response_model=GenerateAlertsOut)
async def generate(
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    created = await generate_alerts(
        SqlAlertRepository(uow.session), GenerateAlertsCommand(business_id=user.business_id)
    )
    await uow.commit()
    return GenerateAlertsOut(created=created)


@router.patch("/{alert_id}/review", response_model=AlertOut)
async def review(
    alert_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    alert = await review_alert(
        SqlAlertRepository(uow.session),
        ReviewAlertCommand(business_id=user.business_id, alert_id=alert_id, user_id=user.user_id),
    )
    await uow.commit()
    return AlertOut(**alert.__dict__)
