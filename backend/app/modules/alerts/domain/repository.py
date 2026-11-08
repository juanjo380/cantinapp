"""Puerto del repositorio de alertas."""
from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.alerts.domain.entities import Alert, DigestItem


class AlertRepository(Protocol):
    async def generate_pending(self, business_id: UUID) -> int: ...

    async def resolve_recovered(self, business_id: UUID) -> int:
        """Marca revisadas (sin usuario = automática) las pendientes cuyo producto volvió a NORMAL."""

    async def unnotified(self, business_id: UUID) -> list[DigestItem]: ...

    async def last_notified_at(self, business_id: UUID) -> datetime | None: ...

    async def mark_notified(self, business_id: UUID, alert_ids: list[UUID]) -> None: ...

    async def list(
        self, business_id: UUID, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Alert], int]: ...

    async def review(self, business_id: UUID, alert_id: UUID, user_id: UUID) -> Alert | None: ...
