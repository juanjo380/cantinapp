"""Adaptador SQLAlchemy del repositorio de alertas.

`generate_pending` crea una alerta por producto en BAJO/AGOTADO sin alerta
pendiente (índice único parcial), enriqueciéndola con la última predicción y
recomendación si existen.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.alerts.domain.entities import Alert, DigestItem
from app.modules.alerts.domain.repository import AlertRepository

_GENERATE_SQL = """
INSERT INTO alerts
    (business_id, product_id, recommendation_id, current_stock, min_stock,
     estimated_demand, recommended_quantity)
SELECT v.business_id, v.product_id, rec.id, v.stock_quantity, v.min_stock,
       f.predicted_demand, rec.suggested_quantity
FROM v_inventory v
LEFT JOIN LATERAL (
    SELECT predicted_demand FROM forecasts
    WHERE business_id = v.business_id AND product_id = v.product_id
    ORDER BY created_at DESC LIMIT 1
) f ON true
LEFT JOIN LATERAL (
    SELECT id, suggested_quantity FROM recommendations
    WHERE business_id = v.business_id AND product_id = v.product_id
    ORDER BY created_at DESC LIMIT 1
) rec ON true
WHERE v.business_id = :business_id AND v.status <> 'NORMAL'
ON CONFLICT (business_id, product_id) WHERE status = 'PENDING' DO NOTHING
"""


def _to_alert(row) -> Alert:
    return Alert(
        id=row["id"],
        product_id=row["product_id"],
        recommendation_id=row["recommendation_id"],
        current_stock=row["current_stock"],
        min_stock=row["min_stock"],
        estimated_demand=row["estimated_demand"],
        recommended_quantity=row["recommended_quantity"],
        status=row["status"],
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
    )


class SqlAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_pending(self, business_id: UUID) -> int:
        result = await self.session.execute(text(_GENERATE_SQL), {"business_id": business_id})
        return result.rowcount or 0

    async def resolve_recovered(self, business_id: UUID) -> int:
        result = await self.session.execute(
            text(
                "UPDATE alerts a SET status = 'REVIEWED', reviewed_at = now() "
                "FROM v_inventory v WHERE a.business_id = :business_id AND a.status = 'PENDING' "
                "AND v.business_id = a.business_id AND v.product_id = a.product_id AND v.status = 'NORMAL'"
            ),
            {"business_id": business_id},
        )
        return result.rowcount or 0

    async def unnotified(self, business_id: UUID) -> list[DigestItem]:
        rows = (
            await self.session.execute(
                text(
                    "SELECT a.id, p.name, a.current_stock, a.min_stock, a.recommended_quantity FROM alerts a "
                    "JOIN products p ON p.business_id = a.business_id AND p.id = a.product_id "
                    "WHERE a.business_id = :business_id AND a.status = 'PENDING' AND a.notified_at IS NULL "
                    "ORDER BY a.current_stock, p.name"
                ),
                {"business_id": business_id},
            )
        ).all()
        return [DigestItem(*row) for row in rows]

    async def last_notified_at(self, business_id: UUID) -> datetime | None:
        return (
            await self.session.execute(
                text("SELECT max(notified_at) FROM alerts WHERE business_id = :business_id"),
                {"business_id": business_id},
            )
        ).scalar_one_or_none()

    async def mark_notified(self, business_id: UUID, alert_ids: list[UUID]) -> None:
        await self.session.execute(
            text("UPDATE alerts SET notified_at = now() WHERE business_id = :business_id AND id = ANY(:ids)"),
            {"business_id": business_id, "ids": alert_ids},
        )

    async def list(
        self, business_id: UUID, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Alert], int]:
        condition = "AND status = :status" if status else ""
        params = {"business_id": business_id, **({"status": status.upper()} if status else {})}
        total = (
            await self.session.execute(
                text(f"SELECT count(*) FROM alerts WHERE business_id = :business_id {condition}"), params
            )
        ).scalar_one()
        rows = (
            await self.session.execute(
                text(
                    "SELECT id, product_id, recommendation_id, current_stock, min_stock, estimated_demand, "
                    "recommended_quantity, status, reviewed_at, created_at FROM alerts "
                    f"WHERE business_id = :business_id {condition} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                ),
                {**params, "limit": limit, "offset": offset},
            )
        ).mappings().all()
        return [_to_alert(row) for row in rows], total

    async def review(self, business_id: UUID, alert_id: UUID, user_id: UUID) -> Alert | None:
        row = (
            await self.session.execute(
                text(
                    "UPDATE alerts SET status = 'REVIEWED', reviewed_by = :user_id, reviewed_at = now() "
                    "WHERE id = :alert_id AND business_id = :business_id AND status = 'PENDING' "
                    "RETURNING id, product_id, recommendation_id, current_stock, min_stock, estimated_demand, "
                    "recommended_quantity, status, reviewed_at, created_at"
                ),
                {"business_id": business_id, "alert_id": alert_id, "user_id": user_id},
            )
        ).mappings().first()
        return _to_alert(row) if row else None
