"""CSV de ventas sin duplicados: huella de archivo (409) y huella por fila."""
import asyncio
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import ConflictError
from app.modules.sales.application.commands import ImportSalesCommand
from app.modules.sales.application.handlers import import_sales
from app.modules.sales.domain.dedup import row_hashes, row_key
from tests.test_csv_import import FakeProducts, FakeSales, FakeSession

BUSINESS = uuid4()


def _import(sales, products, content, **flags):
    command = ImportSalesCommand(
        business_id=BUSINESS, file_name="v.csv", content=content, affects_inventory=False, created_by=None, **flags
    )
    return asyncio.run(import_sales(sales, products, FakeSession(), command))


def test_row_key_matches_sql_backfill_format():
    # Debe coincidir con el UPDATE de db/migrations/005_sales_dedup.sql (precio con 2 decimales).
    key = row_key(UUID("00000000-0000-0000-0000-000000000001"), date(2026, 1, 5), 3, Decimal("2500.5"))
    assert key == "00000000-0000-0000-0000-000000000001|2026-01-05|3|2500.50"
    first, second = row_hashes([key, key])
    assert first != second  # dos ventas iguales el mismo día son dos filas distintas


def test_same_file_twice_asks_confirmation_and_then_imports_nothing():
    sales, products = FakeSales(), FakeProducts(["Pan"])
    content = "product,date,quantity\nPan,2026-01-05,2\nPan,2026-01-06,1\n"
    assert _import(sales, products, content).imported_rows == 2

    with pytest.raises(ConflictError):
        _import(sales, products, content)

    again = _import(sales, products, content, confirm_reimport=True)
    assert (again.total_rows, again.imported_rows, again.duplicate_rows, again.error_rows) == (2, 0, 2, 0)
    assert again.status == "COMPLETED"
    assert len(sales.added) == 2


def test_legitimate_repeated_rows_in_one_file_are_all_imported():
    sales, products = FakeSales(), FakeProducts(["Pan"])
    summary = _import(sales, products, "product,date,quantity\n" + "Pan,2026-01-05,1\n" * 3)
    assert (summary.imported_rows, summary.duplicate_rows) == (3, 0)


def test_partially_overlapping_file_imports_only_new_rows():
    sales, products = FakeSales(), FakeProducts(["Pan", "Leche"])
    _import(sales, products, "product,date,quantity\nPan,2026-01-05,1\nLeche,2026-01-05,2\n")
    # misma venta de pan + una segunda venta igual ese día + una venta nueva
    summary = _import(
        sales, products, "product,date,quantity\nPan,2026-01-05,1\nPan,2026-01-05,1\nLeche,2026-01-06,2\n"
    )
    assert (summary.total_rows, summary.imported_rows, summary.duplicate_rows) == (3, 2, 1)


def test_skip_duplicates_false_imports_everything_without_fingerprint():
    sales, products = FakeSales(), FakeProducts(["Pan"])
    content = "product,date,quantity\nPan,2026-01-05,1\n"
    _import(sales, products, content)
    summary = _import(sales, products, content, confirm_reimport=True, skip_duplicates=False)
    assert (summary.imported_rows, summary.duplicate_rows) == (1, 0)
    assert sales.added[-1]["row_hash"] is None
