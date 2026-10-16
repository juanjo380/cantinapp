"""Puerto del repositorio de ventas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.sales.domain.entities import Sale, SaleImport


class SaleRepository(Protocol):
    async def add(
        self,
        *,
        business_id: UUID,
        product_id: UUID,
        sale_date: date,
        quantity: int,
        unit_price: Decimal,
        source: str,
        affects_inventory: bool,
        import_id: UUID | None = None,
        created_by: UUID | None = None,
    ) -> Sale: ...

    async def open_import(
        self, *, business_id: UUID, file_name: str, total_rows: int, affects_inventory: bool, created_by: UUID | None
    ) -> SaleImport: ...

    async def close_import(
        self, *, import_id: UUID, imported_rows: int, errors: list[dict]
    ) -> None: ...

    async def list(
        self,
        business_id: UUID,
        *,
        product_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]: ...
