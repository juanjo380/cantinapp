"""Puerto del repositorio de alertas."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.alerts.domain.entities import Alert


class AlertRepository(Protocol):
    async def generate_pending(self, business_id: UUID) -> int: ...

    async def list(
        self, business_id: UUID, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[Alert], int]: ...

    async def review(self, business_id: UUID, alert_id: UUID, user_id: UUID) -> Alert | None: ...
