"""Parser de CSV de ventas históricas (RF-07). Usa solo la librería estándar.

Columnas esperadas (encabezados sin distinguir mayúsculas):
  product | product_name  (nombre del producto)   o   product_id
  date | sale_date | fecha        (YYYY-MM-DD o DD/MM/YYYY)
  quantity | cantidad             (entero > 0)
  unit_price | price | precio     (opcional, decimal >= 0)
"""
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")

_ALIASES = {
    "product": "product",
    "product_name": "product",
    "nombre": "product",
    "product_id": "product_id",
    "date": "date",
    "sale_date": "date",
    "fecha": "date",
    "quantity": "quantity",
    "cantidad": "quantity",
    "unit_price": "unit_price",
    "price": "unit_price",
    "precio": "unit_price",
}


@dataclass
class ParsedRow:
    row_number: int
    product_name: str | None
    product_id: str | None
    sale_date: date
    quantity: int
    unit_price: Decimal | None


def _parse_date(value: str) -> date | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_csv(content: str) -> tuple[list[ParsedRow], list[dict]]:
    rows: list[ParsedRow] = []
    errors: list[dict] = []

    reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
    if not reader.fieldnames:
        return rows, [{"row": 0, "field": "header", "message": "El archivo está vacío"}]

    header_map = {name: _ALIASES[name.strip().lower()] for name in reader.fieldnames if name.strip().lower() in _ALIASES}
    if "product" not in header_map.values() and "product_id" not in header_map.values():
        return rows, [{"row": 0, "field": "header", "message": "Falta la columna 'product' o 'product_id'"}]
    if "date" not in header_map.values():
        return rows, [{"row": 0, "field": "header", "message": "Falta la columna 'date'"}]
    if "quantity" not in header_map.values():
        return rows, [{"row": 0, "field": "header", "message": "Falta la columna 'quantity'"}]

    for index, raw in enumerate(reader):
        row_number = index + 2  # la fila 1 es el encabezado
        values = {header_map[k]: (v or "").strip() for k, v in raw.items() if k in header_map}
        if not any(values.values()):
            continue

        row_errors = []
        product_name = values.get("product") or None
        product_id = values.get("product_id") or None
        if not product_name and not product_id:
            row_errors.append({"row": row_number, "field": "product", "message": "Falta producto"})

        sale_date = _parse_date(values.get("date", ""))
        if sale_date is None:
            row_errors.append({"row": row_number, "field": "date", "message": "Fecha inválida"})

        quantity = None
        try:
            quantity = int(values.get("quantity", ""))
            if quantity <= 0:
                raise ValueError
        except ValueError:
            row_errors.append({"row": row_number, "field": "quantity", "message": "Cantidad inválida (entero > 0)"})

        unit_price = None
        raw_price = values.get("unit_price", "")
        if raw_price:
            try:
                unit_price = Decimal(raw_price)
                if unit_price < 0:
                    raise InvalidOperation
            except InvalidOperation:
                row_errors.append({"row": row_number, "field": "unit_price", "message": "Precio inválido"})

        if row_errors:
            errors.extend(row_errors)
            continue

        rows.append(
            ParsedRow(
                row_number=row_number,
                product_name=product_name,
                product_id=product_id,
                sale_date=sale_date,
                quantity=quantity,
                unit_price=unit_price,
            )
        )

    return rows, errors
