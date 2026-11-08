"""Parser de CSV de productos (carga masiva del catálogo). Usa solo la librería estándar.

Columnas (encabezados sin distinguir mayúsculas; espacios = '_'; separador ',' o ';'):
  name | nombre | product | producto              (obligatoria)
  price | precio                                  (obligatoria, decimal >= 0; acepta coma decimal)
  category | categoria | categoría                (opcional)
  supplier | proveedor                            (opcional)
  quantity | cantidad | stock | stock_inicial     (opcional, entero >= 0, por defecto 0)
  min_stock | stock_minimo | stock_mínimo         (opcional, entero >= 0, por defecto 0)
  lead_time_days | dias_abastecimiento | días_abastecimiento   (opcional, entero >= 0, por defecto 0)
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.shared.application.csv_utils import dict_reader, header_key, parse_decimal

_ALIASES = {
    **dict.fromkeys(("name", "nombre", "product", "producto", "product_name"), "name"),
    **dict.fromkeys(("price", "precio", "unit_price"), "price"),
    **dict.fromkeys(("category", "categoria", "categoría"), "category"),
    **dict.fromkeys(("supplier", "proveedor"), "supplier"),
    **dict.fromkeys(("quantity", "cantidad", "stock", "stock_inicial"), "quantity"),
    **dict.fromkeys(("min_stock", "stock_minimo", "stock_mínimo"), "min_stock"),
    **dict.fromkeys(("lead_time_days", "dias_abastecimiento", "días_abastecimiento"), "lead_time_days"),
}
# Mismos límites que ProductCreate (api/schemas.py).
_MAX_LEN = {"name": 200, "category": 120, "supplier": 120}

# Plantilla descargable (GET /api/products/import/template); un test verifica que este parser la acepta.
TEMPLATE = (
    "nombre;precio;categoria;proveedor;stock_inicial;stock_minimo;dias_abastecimiento\r\n"
    "Empanada;2500;Comidas;Panadería La Espiga;40;10;1\r\n"
    "Gaseosa 400 ml;3200,50;Bebidas;Distribuidora Central;24;6;3\r\n"
    "Galletas de avena;1800;Paquetes;;30;8;7\r\n"
)


@dataclass
class ParsedProduct:
    row_number: int
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    quantity: int
    min_stock: int
    lead_time_days: int


def parse_products_csv(content: str) -> tuple[list[ParsedProduct], list[dict]]:
    rows: list[ParsedProduct] = []
    errors: list[dict] = []

    reader = dict_reader(content)
    if not reader.fieldnames:
        return rows, [{"row": 0, "field": "header", "message": "El archivo está vacío"}]
    header_map = {name: _ALIASES[header_key(name)] for name in reader.fieldnames if header_key(name) in _ALIASES}
    for required in ("name", "price"):
        if required not in header_map.values():
            return rows, [{"row": 0, "field": "header", "message": f"Falta la columna '{required}'"}]

    seen: set[str] = set()
    for index, raw in enumerate(reader):
        row_number = index + 2  # la fila 1 es el encabezado
        values = {header_map[k]: (v or "").strip() for k, v in raw.items() if k in header_map}
        if not any(values.values()):
            continue

        row_errors = []

        def error(field: str, message: str) -> None:
            row_errors.append({"row": row_number, "field": field, "message": message})

        name = values.get("name", "")
        if not name:
            error("name", "Falta el nombre")
        elif name.lower() in seen:
            error("name", "Nombre repetido en el archivo")
        for field, limit in _MAX_LEN.items():
            if len(values.get(field, "")) > limit:
                error(field, f"Máximo {limit} caracteres")

        price = None
        try:
            price = parse_decimal(values.get("price", ""))
            if price < 0:
                raise InvalidOperation
        except InvalidOperation:
            error("price", "Precio inválido (número >= 0)")

        ints = {}
        for field in ("quantity", "min_stock", "lead_time_days"):
            try:
                ints[field] = int(values.get(field) or 0)
                if ints[field] < 0:
                    raise ValueError
            except ValueError:
                error(field, "Debe ser un entero >= 0")

        if row_errors:
            errors.extend(row_errors)
            continue
        seen.add(name.lower())
        rows.append(
            ParsedProduct(
                row_number=row_number,
                name=name,
                category=values.get("category") or None,
                supplier=values.get("supplier") or None,
                price=price,
                **ints,
            )
        )

    return rows, errors
