"""Las plantillas descargables deben poder cargarse tal cual, con BOM y en el formato de Excel."""
from app.modules.products.application.csv_parser import TEMPLATE as PRODUCTS_TEMPLATE
from app.modules.products.application.csv_parser import parse_products_csv
from app.modules.sales.application.csv_parser import TEMPLATE as SALES_TEMPLATE
from app.modules.sales.application.csv_parser import parse_csv
from app.shared.api.uploads import csv_template_response


def _as_uploaded(response) -> str:
    return response.body.decode("utf-8-sig")  # igual que read_csv_upload


def test_sales_template_parses_without_errors():
    response = csv_template_response(SALES_TEMPLATE, "plantilla-ventas.csv")
    assert response.body.startswith(b"\xef\xbb\xbf")
    assert "attachment" in response.headers["content-disposition"]
    rows, errors = parse_csv(_as_uploaded(response))
    assert errors == [] and len(rows) == 3


def test_products_template_parses_without_errors():
    rows, errors = parse_products_csv(_as_uploaded(csv_template_response(PRODUCTS_TEMPLATE, "p.csv")))
    assert errors == [] and len(rows) == 3
