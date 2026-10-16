"""Adaptador SQLAlchemy de inventario. Lee la vista `v_inventory` (estado
calculado en la BD) y escribe en `inventory_movements` (el trigger ajusta el
stock de forma atómica)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.domain.entities import InventoryItem, InventoryMovement
from app.modules.inventory.domain.repository import InventoryRepository
from app.modules.inventory.infrastructure.models import MovementRecord

_SORT = {"name": "name", "stock": "stock_quantity", "status": "status", "price": "price"}

_ITEM_COLUMNS = """
    product_id, name, category, supplier, price, stock_quantity, min_stock, lead_time_days, status
"""


def _to_item(row) -> InventoryItem:
    return InventoryItem(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        supplier=row["supplier"],
        price=row["price"],
        stock_quantity=row["stock_quantity"],
        min_stock=row["min_stock"],
        lead_time_days=row["lead_time_days"],
        status=row["status"],
    )


class SqlInventoryRepository(InventoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
    ) -> tuple[list[InventoryItem], int]:
        conditions = ["business_id = :business_id"]
        params: dict = {"business_id": business_id}
        if status:
            conditions.append("status = :status")
            params["status"] = status.upper()
        if category:
            conditions.append("lower(category) = lower(:category)")
            params["category"] = category
        if search:
            conditions.append("name ILIKE :search")
            params["search"] = f"%{search}%"
        where = " AND ".join(conditions)

        key, descending = sort or "name", False
        if key.startswith("-"):
            key, descending = key[1:], True
        column = _SORT.get(key, "name")
        order = f"{column} {'DESC' if descending else 'ASC'}"

        total = (
            await self.session.execute(text(f"SELECT count(*) FROM v_inventory WHERE {where}"), params)
        ).scalar_one()
        rows = (
            await self.session.execute(
                text(
                    f"SELECT {_ITEM_COLUMNS} FROM v_inventory WHERE {where} "
                    f"ORDER BY {order} LIMIT :limit OFFSET :offset"
                ),
                {**params, "limit": limit, "offset": offset},
            )
        ).mappings().all()
        return [_to_item(row) for row in rows], total

    async def get(self, business_id: UUID, product_id: UUID) -> InventoryItem | None:
        row = (
            await self.session.execute(
                text(
                    f"SELECT {_ITEM_COLUMNS} FROM v_inventory WHERE business_id = :business_id AND product_id = :product_id"
                ),
                {"business_id": business_id, "product_id": product_id},
            )
        ).mappings().first()
        return _to_item(row) if row else None

    async def list_movements(
        self, business_id: UUID, product_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[InventoryMovement], int]:
        where = "business_id = :business_id AND product_id = :product_id"
        params = {"business_id": business_id, "product_id": product_id}
        total = (
            await self.session.execute(
                text(f"SELECT count(*) FROM inventory_movements WHERE {where}"), params
            )
        ).scalar_one()
        rows = (
            await self.session.execute(
                text(
                    "SELECT id, product_id, movement_type, quantity_change, stock_after, notes, created_at "
                    f"FROM inventory_movements WHERE {where} ORDER BY created_at DESC, id DESC "
                    "LIMIT :limit OFFSET :offset"
                ),
                {**params, "limit": limit, "offset": offset},
            )
        ).mappings().all()
        items = [
            InventoryMovement(
                id=row["id"],
                product_id=row["product_id"],
                movement_type=row["movement_type"],
                quantity_change=row["quantity_change"],
                stock_after=row["stock_after"],
                notes=row["notes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return items, total

    async def add_movement(
        self,
        *,
        business_id: UUID,
        product_id: UUID,
        movement_type: str,
        quantity_change: int,
        notes: str | None,
        created_by: UUID | None,
    ) -> InventoryMovement:
        record = MovementRecord(
            business_id=business_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity_change=quantity_change,
            notes=notes,
            created_by=created_by,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return InventoryMovement(
            id=record.id,
            product_id=record.product_id,
            movement_type=record.movement_type,
            quantity_change=record.quantity_change,
            stock_after=record.stock_after,
            notes=record.notes,
            created_at=record.created_at,
        )
