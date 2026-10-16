"""Handlers de alertas."""
from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.alerts.application.commands import GenerateAlertsCommand, ReviewAlertCommand
from app.modules.alerts.application.queries import ListAlertsQuery
from app.modules.alerts.domain.repository import AlertRepository
from app.shared.domain.repository import Page


async def generate_alerts(alerts: AlertRepository, command: GenerateAlertsCommand) -> int:
    return await alerts.generate_pending(command.business_id)


async def list_alerts(alerts: AlertRepository, query: ListAlertsQuery) -> Page:
    if query.status and query.status.upper() not in ("PENDING", "REVIEWED"):
        raise UnprocessableError("status debe ser PENDING o REVIEWED")
    items, total = await alerts.list(
        query.business_id, status=query.status, limit=query.limit, offset=query.offset
    )
    return Page(items=items, total=total, limit=query.limit, offset=query.offset)


async def review_alert(alerts: AlertRepository, command: ReviewAlertCommand):
    alert = await alerts.review(command.business_id, command.alert_id, command.user_id)
    if alert is None:
        raise NotFoundError("Alerta pendiente no encontrada")
    return alert
