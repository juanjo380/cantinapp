"""Puerto del repositorio de inventario."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.inventory.domain.entities import InventoryItem, InventoryMovement


class InventoryRepository(Protocol):
    async def list(
        self,
        business_id: UUID,
        *,
        status: str | None = None,
        category: str | None = None,
        search: str | None = None,
        sort: str = "name",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InventoryItem], int]: ...

    async def get(self, business_id: UUID, product_id: UUID) -> InventoryItem | None: ...

    async def list_movements(
        self, business_id: UUID, product_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[InventoryMovement], int]: ...

    async def add_movement(
        self,
        *,
        business_id: UUID,
        product_id: UUID,
        movement_type: str,
        quantity_change: int,
        notes: str | None,
        created_by: UUID | None,
    ) -> InventoryMovement: ...
