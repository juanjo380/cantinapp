"""Handlers de ventas. El descuento de inventario (RF-08) lo hace el trigger
`trg_sales_inventory` de la base de datos al insertar la venta."""
import logging
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.modules.products.domain.repository import ProductRepository
from app.modules.sales.application.commands import CreateSaleCommand, ImportSalesCommand
from app.modules.sales.application.csv_parser import parse_csv
from app.modules.sales.domain.dedup import file_hash, row_hashes, row_key
from app.modules.sales.domain.entities import Sale, SaleImport
from app.modules.sales.domain.repository import SaleRepository

logger = logging.getLogger("cantinapp")
_DEDUP_INDEX = "ux_sales_business_row_hash"


async def register_sale(
    sales: SaleRepository, products: ProductRepository, command: CreateSaleCommand
) -> Sale:
    product = await products.get(command.business_id, command.product_id)
    if product is None or not product.is_active:
        raise NotFoundError("Producto no encontrado")
    if product.stock_quantity < command.quantity:
        raise UnprocessableError(f"Stock insuficiente: disponible {product.stock_quantity}")
    return await sales.add(
        business_id=command.business_id,
        product_id=command.product_id,
        sale_date=command.sale_date,
        quantity=command.quantity,
        unit_price=command.unit_price if command.unit_price is not None else product.price,
        source="MANUAL",
        affects_inventory=True,
        created_by=command.created_by,
        location_id=command.location_id,
    )


async def import_sales(
    sales: SaleRepository, products: ProductRepository, session: AsyncSession, command: ImportSalesCommand
) -> SaleImport:
    parsed, errors = parse_csv(command.content)
    content_hash = file_hash(command.content)
    if not command.confirm_reimport:
        previous = await sales.find_import_by_hash(command.business_id, content_hash)
        if previous is not None:
            raise ConflictError(
                f"Este archivo ya se importó el {previous:%d/%m/%Y}. "
                "Si de verdad quieres cargarlo otra vez, confirma la reimportación."
            )
    summary = await sales.open_import(
        business_id=command.business_id,
        file_name=command.file_name,
        total_rows=len(parsed) + len({e["row"] for e in errors}),
        affects_inventory=command.affects_inventory,
        created_by=command.created_by,
        file_hash=content_hash,
    )

    valid = []
    resolved: dict[tuple[str | None, str | None], object] = {}  # un CSV repite productos: una consulta por producto
    for row in parsed:
        key = (row.product_id, row.product_name)
        if key not in resolved:
            resolved[key] = await _resolve_product(products, command.business_id, row)
        product = resolved[key]
        if product is None:
            errors.append({"row": row.row_number, "field": "product", "message": "Producto no encontrado"})
            continue
        unit_price = row.unit_price if row.unit_price is not None else product.price
        valid.append((row, product, unit_price))

    hashes = row_hashes([row_key(p.id, r.sale_date, r.quantity, price) for r, p, price in valid])
    existing = await sales.existing_row_hashes(command.business_id, hashes) if command.skip_duplicates else set()

    imported = duplicates = 0
    for (row, product, unit_price), row_hash in zip(valid, hashes):
        if row_hash in existing:
            duplicates += 1
            continue
        try:
            async with session.begin_nested():
                await sales.add(
                    business_id=command.business_id,
                    product_id=product.id,
                    sale_date=row.sale_date,
                    quantity=row.quantity,
                    unit_price=unit_price,
                    source="CSV",
                    affects_inventory=command.affects_inventory,
                    import_id=summary.id,
                    created_by=command.created_by,
                    # sin huella = duplicado intencional: ni bloquea ni lo bloquean cargas futuras
                    row_hash=row_hash if command.skip_duplicates else None,
                    location_id=command.location_id,
                )
            imported += 1
        except IntegrityError as exc:
            if _DEDUP_INDEX in str(exc.orig):  # otra carga simultánea insertó la misma fila
                duplicates += 1
            else:
                errors.append({"row": row.row_number, "field": "stock", "message": "Stock insuficiente"})

    await sales.close_import(
        import_id=summary.id, imported_rows=imported, duplicate_rows=duplicates, errors=errors
    )
    summary.imported_rows = imported
    summary.duplicate_rows = duplicates
    summary.error_rows = len({e["row"] for e in errors})
    summary.errors = errors
    summary.status = "COMPLETED" if imported > 0 or not errors else "FAILED"
    return summary


async def list_sales(
    sales: SaleRepository,
    business_id: UUID,
    *,
    product_id: UUID | None = None,
    location_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return await sales.list(
        business_id,
        product_id=product_id,
        location_id=location_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


async def _resolve_product(products: ProductRepository, business_id: UUID, row):
    if row.product_id:
        try:
            product_id = UUID(row.product_id)
        except ValueError:
            return None
        return await products.get(business_id, product_id)
    return await products.get_by_name(business_id, row.product_name)
