"""Adaptador SQLAlchemy del repositorio de productos.

Categoría y proveedor se manejan como texto en la API (HU02) y se resuelven
contra los catálogos por nombre (get-or-create) en esta capa.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.domain.discounts import ActiveDiscount, DiscountCandidate, discount_percent
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
        composite: bool | None = None,
        sort: str = "name",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        category_name = func.coalesce(CategoryRecord.name, None)

        conditions = [ProductRecord.business_id == business_id]
        if active_only:
            conditions.append(ProductRecord.is_active.is_(True))
        if composite is not None:
            conditions.append(ProductRecord.is_composite.is_(composite))
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
        is_composite: bool = False,
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
            is_composite=is_composite,
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
        for field in ("name", "price", "min_stock", "lead_time_days", "is_active"):
            if changes.get(field) is not None:
                setattr(record, field, changes[field])
        await self.session.flush()
        return await self.get(product.business_id, product.id)

    async def deactivate(self, product: Product) -> None:
        record = await self.session.get(ProductRecord, product.id)
        record.is_active = False
        await self.session.flush()

    async def discount_candidates(self, business_id: UUID, *, days: int) -> list[DiscountCandidate]:
        # Unidades por sale_date (no por fecha de inserción: los CSV históricos se cargan hoy). Las ventas de
        # un compuesto cuentan como salida de sus componentes, igual que el trigger de inventario (010).
        rows = (
            await self.session.execute(
                text(
                    "WITH moved AS ("
                    " SELECT COALESCE(pc.component_id, s.product_id) AS product_id,"
                    "  SUM(s.quantity * COALESCE(pc.quantity, 1)) FILTER ("
                    "   WHERE s.sale_date > CURRENT_DATE - CAST(:days AS int)) AS units,"
                    "  MIN(s.sale_date) AS first_sale, MAX(s.sale_date) AS last_sale"
                    " FROM sales s"
                    " LEFT JOIN product_components pc ON pc.business_id = s.business_id AND pc.product_id = s.product_id"
                    "  AND (SELECT composites_enabled FROM businesses WHERE id = :b)"
                    " WHERE s.business_id = :b GROUP BY 1"
                    ") "
                    "SELECT p.id, p.name, c.name AS category, p.price, p.stock_quantity AS stock,"
                    " COALESCE(o.units, 0)::int AS units, o.last_sale,"
                    " (p.price_before_discount > p.price"
                    "  OR COALESCE(p.last_discount_at > now() - make_interval(days => CAST(:days AS int)), false))"
                    "  AS recently_discounted "
                    "FROM products p "
                    "LEFT JOIN categories c ON c.id = p.category_id "
                    "LEFT JOIN moved o ON o.product_id = p.id "
                    "WHERE p.business_id = :b AND p.is_active AND NOT p.is_composite"
                    " AND LEAST(p.created_at::date, o.first_sale) <= CURRENT_DATE - CAST(:days AS int)"
                ),
                {"b": business_id, "days": days},
            )
        ).mappings().all()
        return [
            DiscountCandidate(
                product_id=r["id"], name=r["name"], category=r["category"], price=r["price"], stock=r["stock"],
                units=r["units"], last_sale=r["last_sale"], recently_discounted=r["recently_discounted"],
            )
            for r in rows
        ]

    async def active_discounts(self, business_id: UUID) -> list[ActiveDiscount]:
        rows = (
            await self.session.execute(
                text(
                    "SELECT id, price, price_before_discount, last_discount_at FROM products "
                    "WHERE business_id = :b AND price_before_discount > price"
                ),
                {"b": business_id},
            )
        ).mappings().all()
        return [
            ActiveDiscount(
                product_id=r["id"],
                price_before=r["price_before_discount"],
                percent=discount_percent(r["price_before_discount"], r["price"]),
                discounted_at=r["last_discount_at"],
            )
            for r in rows
        ]

    async def list_price(self, product: Product) -> Decimal:
        """Precio sin descuento: el guardado si hay un descuento activo, si no el actual."""
        before = (
            await self.session.execute(
                # Si el precio se editó a mano por encima del de lista, el guardado ya no aplica.
                text(
                    "SELECT price_before_discount FROM products "
                    "WHERE business_id = :b AND id = :p AND price_before_discount > price"
                ),
                {"b": product.business_id, "p": product.id},
            )
        ).scalar_one_or_none()
        return before if before is not None else product.price

    async def apply_discount(self, product: Product, new_price: Decimal) -> Product:
        # GREATEST (ignora NULL): un segundo descuento conserva el precio de lista original.
        await self.session.execute(
            text(
                "UPDATE products SET price_before_discount = GREATEST(price_before_discount, price), "
                "price = :price, last_discount_at = now() WHERE business_id = :b AND id = :p"
            ),
            {"price": new_price, "b": product.business_id, "p": product.id},
        )
        self.session.expire_all()  # el ORM no ve el UPDATE por SQL
        return await self.get(product.business_id, product.id)

    async def remove_discount(self, product: Product) -> Product | None:
        """Vuelve al precio de lista. None si el producto no tenía descuento activo."""
        restored = (
            await self.session.execute(
                text(
                    "UPDATE products SET price = price_before_discount, price_before_discount = NULL "
                    "WHERE business_id = :b AND id = :p AND price_before_discount > price RETURNING id"
                ),
                {"b": product.business_id, "p": product.id},
            )
        ).scalar_one_or_none()
        if restored is None:
            return None
        self.session.expire_all()
        return await self.get(product.business_id, product.id)

    async def composites_enabled(self, business_id: UUID) -> bool:
        return bool(
            (
                await self.session.execute(
                    text("SELECT composites_enabled FROM businesses WHERE id = :b"), {"b": business_id}
                )
            ).scalar_one_or_none()
        )

    async def list_composites(self, business_id: UUID) -> list[dict]:
        rows = (
            await self.session.execute(
                text(
                    "SELECT p.id AS product_id, p.name, p.price, pc.component_id, c.name AS component_name, "
                    "pc.quantity, c.stock_quantity AS component_stock "
                    "FROM products p "
                    "LEFT JOIN product_components pc ON pc.product_id = p.id "
                    "LEFT JOIN products c ON c.id = pc.component_id "
                    "WHERE p.business_id = :b AND p.is_composite AND p.is_active "
                    "ORDER BY lower(p.name), lower(c.name)"
                ),
                {"b": business_id},
            )
        ).mappings().all()
        composites: dict[UUID, dict] = {}
        for row in rows:
            item = composites.setdefault(
                row["product_id"],
                {"product_id": row["product_id"], "name": row["name"], "price": row["price"], "components": []},
            )
            if row["component_id"] is None:  # compuesto aún sin receta
                continue
            item["components"].append(
                {
                    "component_id": row["component_id"],
                    "name": row["component_name"],
                    "quantity": row["quantity"],
                    "stock_quantity": row["component_stock"],
                }
            )
        for item in composites.values():  # cuántos se pueden armar con el stock actual
            item["available"] = min((c["stock_quantity"] // c["quantity"] for c in item["components"]), default=0)
        return list(composites.values())

    async def set_components(self, business_id: UUID, product_id: UUID, items: dict[UUID, int]) -> None:
        params = {"b": business_id, "p": product_id}
        await self.session.execute(
            text("DELETE FROM product_components WHERE business_id = :b AND product_id = :p"), params
        )
        if items:
            await self.session.execute(
                text(
                    "INSERT INTO product_components (business_id, product_id, component_id, quantity) "
                    "VALUES (:b, :p, :c, :q)"
                ),
                [{**params, "c": component_id, "q": quantity} for component_id, quantity in items.items()],
            )
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
        is_composite=record.is_composite,
    )
