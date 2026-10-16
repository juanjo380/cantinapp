"""Handlers de ventas. El descuento de inventario (RF-08) lo hace el trigger
`trg_sales_inventory` de la base de datos al insertar la venta."""
import logging
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.products.domain.repository import ProductRepository
from app.modules.sales.application.commands import CreateSaleCommand, ImportSalesCommand
from app.modules.sales.application.csv_parser import parse_csv
from app.modules.sales.domain.entities import Sale, SaleImport
from app.modules.sales.domain.repository import SaleRepository

logger = logging.getLogger("cantinapp")


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
    )


async def import_sales(
    sales: SaleRepository, products: ProductRepository, session: AsyncSession, command: ImportSalesCommand
) -> SaleImport:
    parsed, errors = parse_csv(command.content)
    summary = await sales.open_import(
        business_id=command.business_id,
        file_name=command.file_name,
        total_rows=len(parsed) + len({e["row"] for e in errors}),
        affects_inventory=command.affects_inventory,
        created_by=command.created_by,
    )

    imported = 0
    for row in parsed:
        product = await _resolve_product(products, command.business_id, row)
        if product is None:
            errors.append({"row": row.row_number, "field": "product", "message": "Producto no encontrado"})
            continue
        unit_price = row.unit_price if row.unit_price is not None else product.price
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
                )
            imported += 1
        except IntegrityError:
            errors.append({"row": row.row_number, "field": "stock", "message": "Stock insuficiente"})

    await sales.close_import(import_id=summary.id, imported_rows=imported, errors=errors)
    summary.imported_rows = imported
    summary.error_rows = len(errors)
    summary.errors = errors
    summary.status = "COMPLETED" if imported > 0 or not errors else "FAILED"
    return summary


async def list_sales(
    sales: SaleRepository,
    business_id: UUID,
    *,
    product_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    return await sales.list(
        business_id,
        product_id=product_id,
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
