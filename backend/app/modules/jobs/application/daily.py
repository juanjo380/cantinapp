"""Trabajo diario por negocio: resolver alertas de productos que ya se repusieron, generar las
nuevas, recalcular co-ocurrencias y enviar un único correo-resumen a dueño y administradores.

Lo dispara POST /api/internal/jobs/daily (GitHub Actions) o `python -m scripts.run_daily_jobs`.
Cada negocio usa sus propias sesiones: si uno falla, se registra y se sigue con los demás.
No regenera predicciones (sería una por producto): las alertas usan la última que exista.
"""
import logging
from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import UnprocessableError
from app.core.mailer import MailError, alerts_digest_email, send_email
from app.modules.alerts.infrastructure.repository import SqlAlertRepository
from app.modules.jobs.domain.policy import should_send_digest
from app.modules.jobs.infrastructure.repository import SqlJobsRepository
from app.modules.recommendations.application.facade import run_cooccurrence_job
from app.shared.infrastructure.database import SessionFactory

logger = logging.getLogger("cantinapp.jobs")


async def run_for_business(business_id: UUID) -> dict:
    async with SessionFactory() as session:
        alerts = SqlAlertRepository(session)
        resolved = await alerts.resolve_recovered(business_id)
        created = await alerts.generate_pending(business_id)
        await session.commit()

    try:
        pairs = await run_cooccurrence_job(business_id)
    except UnprocessableError:  # menos de 30 días de historial: no es un fallo
        pairs = None

    emailed = 0
    async with SessionFactory() as session:
        alerts = SqlAlertRepository(session)
        pending = await alerts.unnotified(business_id)
        if should_send_digest(pending, await alerts.last_notified_at(business_id), datetime.now(UTC)):
            name, recipients = await SqlJobsRepository(session).digest_target(business_id)
            subject, text, html = alerts_digest_email(
                name,
                [(a.product_name, a.current_stock, a.min_stock, a.recommended_quantity) for a in pending],
                f"{get_settings().frontend_url.rstrip('/')}/alertas",
            )
            for to in recipients:
                try:
                    await send_email(to, subject, text, html)
                    emailed += 1
                except MailError:
                    pass  # send_email ya dejó el detalle en el log
            if emailed:  # si nadie recibió el correo, mañana se reintenta con las mismas alertas
                await alerts.mark_notified(business_id, [a.alert_id for a in pending])
                await session.commit()

    return {"resolved": resolved, "created": created, "cooccurrence_pairs": pairs, "emailed": emailed}


async def run_daily_jobs(business_ids: list[UUID] | None = None, run_one=run_for_business) -> list[dict]:
    if business_ids is None:
        async with SessionFactory() as session:
            business_ids = await SqlJobsRepository(session).business_ids()

    results = []
    for business_id in business_ids:
        try:
            outcome = {"business_id": str(business_id), "ok": True, **await run_one(business_id)}
            logger.info("Trabajo diario %s: %s", business_id, outcome)
        except Exception as exc:  # noqa: BLE001 - un negocio que falla no detiene a los demás
            logger.exception("Trabajo diario %s falló", business_id)
            outcome = {"business_id": str(business_id), "ok": False, "error": type(exc).__name__}
        results.append(outcome)
    return results
