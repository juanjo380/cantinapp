"""Adaptador SQLAlchemy del repositorio de productos.

Categoría y proveedor se manejan como texto en la API (HU02) y se resuelven
contra los catálogos por nombre (get-or-create) en esta capa.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.domain.entities import Product
from app.modules.products.domain.repository import ProductRepository
from app.modules.products.infrastructure.models import CategoryRecord, ProductRecord, SupplierRecord

_SORT_COLUMNS = {
    "name": ProductRecord.name,
    "price": ProductRecord.price,
    "stock": ProductRecord.stock_quantity,
    "created": ProductRecord.created_at,
}


class SqlProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        business_id: UUID,
        *,
        search: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        sort: str = "name",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        category_name = func.coalesce(CategoryRecord.name, None)

        conditions = [ProductRecord.business_id == business_id]
        if active_only:
            conditions.append(ProductRecord.is_active.is_(True))
        if search:
            conditions.append(ProductRecord.name.ilike(f"%{search}%"))
        if category:
            conditions.append(func.lower(category_name) == category.lower())

        base = (
            select(ProductRecord, category_name.label("category"), SupplierRecord.name.label("supplier"))
            .outerjoin(CategoryRecord, CategoryRecord.id == ProductRecord.category_id)
            .outerjoin(SupplierRecord, SupplierRecord.id == ProductRecord.supplier_id)
            .where(*conditions)
        )

        column, descending = _SORT_COLUMNS.get("name"), False
        sort_key = sort or "name"
        if sort_key.startswith("-"):
            sort_key, descending = sort_key[1:], True
        column = _SORT_COLUMNS.get(sort_key, ProductRecord.name)
        base = base.order_by(column.desc() if descending else column.asc())

        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (await self.session.execute(base.limit(limit).offset(offset))).all()
        return [_to_product(*row) for row in rows], total

    async def get(self, business_id: UUID, product_id: UUID) -> Product | None:
        row = (
            await self.session.execute(
                select(
                    ProductRecord,
                    CategoryRecord.name.label("category"),
                    SupplierRecord.name.label("supplier"),
                )
                .outerjoin(CategoryRecord, CategoryRecord.id == ProductRecord.category_id)
                .outerjoin(SupplierRecord, SupplierRecord.id == ProductRecord.supplier_id)
                .where(ProductRecord.business_id == business_id, ProductRecord.id == product_id)
            )
        ).first()
        return _to_product(*row) if row else None

    async def get_by_name(self, business_id: UUID, name: str) -> Product | None:
        record = (
            await self.session.execute(
                select(ProductRecord).where(
                    ProductRecord.business_id == business_id,
                    ProductRecord.is_active.is_(True),
                    func.lower(ProductRecord.name) == name.strip().lower(),
                )
            )
        ).scalar_one_or_none()
        return _to_product(record) if record else None

    async def add(
        self,
        *,
        business_id: UUID,
        name: str,
        category: str | None,
        supplier: str | None,
        price: Decimal,
        quantity: int,
        min_stock: int,
        lead_time_days: int,
    ) -> Product:
        record = ProductRecord(
            business_id=business_id,
            category_id=await self._resolve_category(business_id, category),
            supplier_id=await self._resolve_supplier(business_id, supplier),
            name=name.strip(),
            price=price,
            stock_quantity=quantity,
            min_stock=min_stock,
            lead_time_days=lead_time_days,
        )
        self.session.add(record)
        await self.session.flush()
        return _to_product(record, category, supplier)

    async def update(self, product: Product, changes: dict) -> Product:
        record = await self.session.get(ProductRecord, product.id)
        if "category" in changes:
            record.category_id = await self._resolve_category(product.business_id, changes["category"])
        if "supplier" in changes:
            record.supplier_id = await self._resolve_supplier(product.business_id, changes["supplier"])
        for field in ("name", "price", "min_stock", "lead_time_days"):
            if changes.get(field) is not None:
                setattr(record, field, changes[field])
        await self.session.flush()
        return await self.get(product.business_id, product.id)

    async def deactivate(self, product: Product) -> None:
        record = await self.session.get(ProductRecord, product.id)
        record.is_active = False
        await self.session.flush()

    async def _resolve_category(self, business_id: UUID, name: str | None) -> UUID | None:
        return await _resolve_catalog(self.session, CategoryRecord, business_id, name)

    async def _resolve_supplier(self, business_id: UUID, name: str | None) -> UUID | None:
        return await _resolve_catalog(self.session, SupplierRecord, business_id, name)


async def _resolve_catalog(session: AsyncSession, model, business_id: UUID, name: str | None) -> UUID | None:
    if not name or not name.strip():
        return None
    existing = (
        await session.execute(
            select(model.id).where(model.business_id == business_id, func.lower(model.name) == name.strip().lower())
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    record = model(business_id=business_id, name=name.strip())
    session.add(record)
    await session.flush()
    return record.id


def _to_product(record: ProductRecord, category: str | None = None, supplier: str | None = None) -> Product:
    return Product(
        id=record.id,
        business_id=record.business_id,
        name=record.name,
        category=category,
        supplier=supplier,
        price=record.price,
        stock_quantity=record.stock_quantity,
        min_stock=record.min_stock,
        lead_time_days=record.lead_time_days,
        is_active=record.is_active,
    )
