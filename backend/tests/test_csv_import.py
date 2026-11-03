import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import UploadFile

from app.core.exceptions import UnprocessableError
from app.modules.products.application.commands import ImportProductsCommand
from app.modules.products.application.csv_parser import parse_products_csv
from app.modules.products.application.handlers import import_products
from app.modules.sales.application.commands import ImportSalesCommand
from app.modules.sales.application.csv_parser import parse_csv
from app.modules.sales.application.handlers import import_sales
from app.shared.api import uploads
from app.shared.application.csv_utils import parse_decimal


class FakeSession:
    @asynccontextmanager
    async def begin_nested(self):
        yield


# --- utilidades compartidas -------------------------------------------------

def test_parse_decimal_accepts_spanish_formats_and_rejects_non_finite():
    assert parse_decimal("2500") == Decimal("2500")
    assert parse_decimal("2500,50") == Decimal("2500.50")
    assert parse_decimal("$ 2.500,50") == Decimal("2500.50")
    for bad in ("NaN", "Infinity", "abc", ""):
        with pytest.raises(InvalidOperation):
            parse_decimal(bad)


def test_upload_decodes_excel_ansi_and_enforces_size(monkeypatch):
    ansi = "nombre;precio\nPiña;2500\n".encode("cp1252")
    assert "Piña" in asyncio.run(uploads.read_csv_upload(UploadFile(file=BytesIO(ansi))))
    monkeypatch.setattr(uploads, "MAX_CSV_BYTES", 5)
    with pytest.raises(UnprocessableError):
        asyncio.run(uploads.read_csv_upload(UploadFile(file=BytesIO(ansi))))


# --- ventas -------------------------------------------------------------------

def test_sales_csv_from_spanish_excel_semicolon_and_comma_decimal():
    rows, errors = parse_csv("﻿Producto;Fecha;Cantidad;Precio\nPan;05/01/2026;3;2500,50\n")
    assert errors == []
    assert (rows[0].product_name, rows[0].quantity, rows[0].unit_price) == ("Pan", 3, Decimal("2500.50"))


class FakeSales:
    def __init__(self):
        self.added = []

    async def open_import(self, **kwargs):
        return SimpleNamespace(id=uuid4(), **kwargs)

    async def close_import(self, *, import_id, imported_rows, errors):
        pass

    async def add(self, **kwargs):
        self.added.append(kwargs)


class FakeProducts:
    def __init__(self, names=()):
        self.by_name = {
            n.lower(): SimpleNamespace(id=uuid4(), name=n, price=Decimal("1000")) for n in names
        }
        self.added = []

    async def get_by_name(self, business_id, name):
        return self.by_name.get(name.strip().lower())

    async def add(self, **kwargs):
        self.added.append(kwargs)


def test_sales_import_counts_rows_with_errors_not_errors():
    sales, products = FakeSales(), FakeProducts(["Pan"])
    content = "product,date,quantity\nPan,2026-01-05,2\nPan,mala,0\nNoExiste,2026-01-05,1\n"
    command = ImportSalesCommand(
        business_id=uuid4(), file_name="v.csv", content=content, affects_inventory=False, created_by=None
    )
    summary = asyncio.run(import_sales(sales, products, FakeSession(), command))
    assert (summary.total_rows, summary.imported_rows, summary.error_rows) == (3, 1, 2)
    assert sales.added[0]["unit_price"] == Decimal("1000")  # sin precio usa el del producto


# --- productos ----------------------------------------------------------------

def test_products_csv_with_spanish_headers_and_defaults():
    content = "Nombre;Precio;Categoría;Stock inicial;Stock mínimo\nArroz;3200,5;Granos;10;2\nSal;900;;;\n"
    rows, errors = parse_products_csv(content)
    assert errors == []
    assert (rows[0].name, rows[0].price, rows[0].category, rows[0].quantity, rows[0].min_stock) == (
        "Arroz", Decimal("3200.5"), "Granos", 10, 2
    )
    assert (rows[1].category, rows[1].quantity, rows[1].lead_time_days) == (None, 0, 0)


def test_products_csv_reports_bad_rows_and_duplicates():
    content = "name,price,quantity\nPan,100,1\npan,200,1\n,abc,-1\n"
    rows, errors = parse_products_csv(content)
    assert [r.name for r in rows] == ["Pan"]
    assert {(e["row"], e["field"]) for e in errors} == {(3, "name"), (4, "name"), (4, "price"), (4, "quantity")}


def test_products_csv_requires_name_and_price_headers():
    _, errors = parse_products_csv("nombre,stock\nPan,1\n")
    assert errors == [{"row": 0, "field": "header", "message": "Falta la columna 'price'"}]


def test_products_import_skips_existing_names_and_summarizes():
    products = FakeProducts(["Pan"])
    command = ImportProductsCommand(
        business_id=uuid4(), file_name="p.csv", content="name,price\nPan,100\nLeche,3000\n,5\n"
    )
    summary = asyncio.run(import_products(products, FakeSession(), command))
    assert [p["name"] for p in products.added] == ["Leche"]
    assert (summary.total_rows, summary.imported_rows, summary.error_rows, summary.status) == (3, 1, 2, "COMPLETED")
    assert [e["row"] for e in summary.errors] == [2, 4]
