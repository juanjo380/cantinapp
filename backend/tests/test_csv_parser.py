from datetime import date
from decimal import Decimal

from app.modules.sales.application.csv_parser import parse_csv


def test_valid_csv_is_parsed():
    content = "product,date,quantity,unit_price\nCoca-Cola,2026-01-05,10,2500\n"
    rows, errors = parse_csv(content)
    assert errors == []
    assert rows[0].product_name == "Coca-Cola"
    assert rows[0].sale_date == date(2026, 1, 5)
    assert rows[0].quantity == 10
    assert rows[0].unit_price == Decimal("2500")


def test_accepts_spanish_headers_and_dates():
    content = "nombre,fecha,cantidad\nPan,05/01/2026,3\n"
    rows, errors = parse_csv(content)
    assert errors == []
    assert rows[0].sale_date == date(2026, 1, 5)


def test_invalid_rows_are_reported_with_line_and_field():
    content = "product,date,quantity\nPan,no-es-fecha,0\n"
    _, errors = parse_csv(content)
    fields = {(e["row"], e["field"]) for e in errors}
    assert (2, "date") in fields
    assert (2, "quantity") in fields


def test_missing_required_header_fails():
    _, errors = parse_csv("producto,cantidad\nPan,3\n")
    assert errors and errors[0]["field"] == "header"
