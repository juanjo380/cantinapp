"""Adaptador SQLAlchemy del repositorio de ventas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.infrastructure.models import ProductRecord
from app.modules.sales.domain.entities import Sale, SaleImport
from app.modules.sales.domain.repository import SaleRepository
from app.modules.sales.infrastructure.models import SaleImportRecord, SaleRecord


class SqlSaleRepository(SaleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
    ) -> Sale:
        record = SaleRecord(
            business_id=business_id,
            product_id=product_id,
            sale_date=sale_date,
            quantity=quantity,
            unit_price=unit_price,
            source=source,
            affects_inventory=affects_inventory,
            import_id=import_id,
            created_by=created_by,
        )
        self.session.add(record)
        await self.session.flush()
        return Sale(
            id=record.id,
            business_id=business_id,
            product_id=product_id,
            sale_date=sale_date,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=(unit_price * quantity),
            source=source,
            affects_inventory=affects_inventory,
        )

    async def open_import(
        self, *, business_id: UUID, file_name: str, total_rows: int, affects_inventory: bool, created_by
    ) -> SaleImport:
        record = SaleImportRecord(
            business_id=business_id,
            file_name=file_name,
            total_rows=total_rows,
            status="PROCESSING",
            created_by=created_by,
        )
        self.session.add(record)
        await self.session.flush()
        return SaleImport(
            id=record.id,
            file_name=file_name,
            total_rows=total_rows,
            imported_rows=0,
            error_rows=0,
            status="PROCESSING",
            affects_inventory=affects_inventory,
        )

    async def close_import(self, *, import_id: UUID, imported_rows: int, errors: list[dict]) -> None:
        record = await self.session.get(SaleImportRecord, import_id)
        record.imported_rows = imported_rows
        record.error_rows = len(errors)
        record.error_detail = errors or None
        record.status = "COMPLETED" if imported_rows > 0 or not errors else "FAILED"
        await self.session.flush()

    async def list(
        self,
        business_id: UUID,
        *,
        product_id: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        conditions = [SaleRecord.business_id == business_id]
        if product_id:
            conditions.append(SaleRecord.product_id == product_id)
        if date_from:
            conditions.append(SaleRecord.sale_date >= date_from)
        if date_to:
            conditions.append(SaleRecord.sale_date <= date_to)

        base = (
            select(
                SaleRecord.id,
                SaleRecord.product_id,
                ProductRecord.name.label("product_name"),
                SaleRecord.sale_date,
                SaleRecord.quantity,
                SaleRecord.unit_price,
                SaleRecord.total_amount,
                SaleRecord.source,
                SaleRecord.affects_inventory,
            )
            .join(ProductRecord, ProductRecord.id == SaleRecord.product_id)
            .where(*conditions)
            .order_by(SaleRecord.sale_date.desc(), SaleRecord.created_at.desc())
        )
        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = (await self.session.execute(base.limit(limit).offset(offset))).mappings().all()
        return [dict(row) for row in rows], total
