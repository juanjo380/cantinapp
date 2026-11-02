"""Lectura tolerante de CSV exportados desde Excel (ventas y productos). Solo librería estándar."""
import csv
import io
from decimal import Decimal, InvalidOperation


def header_key(name: str) -> str:
    """'Stock mínimo ' -> 'stock_mínimo': los encabezados se comparan sin mayúsculas ni espacios."""
    return name.strip().lower().replace(" ", "_")


def dict_reader(content: str) -> csv.DictReader:
    content = content.lstrip("﻿")
    # Excel con configuración regional en español (es-CO) separa columnas con ';' en vez de ','.
    first_line = content.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    return csv.DictReader(io.StringIO(content), delimiter=delimiter)


def parse_decimal(value: str) -> Decimal:
    """Acepta 2500, 2500.50, 2500,50, 2.500,50 y $2500. Lanza InvalidOperation si no es un número finito."""
    text = value.strip().replace("$", "").replace(" ", "")
    if "," in text and "." in text:  # 2.500,50: punto de miles y coma decimal
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:  # 2500,50
        text = text.replace(",", ".")
    number = Decimal(text)
    if not number.is_finite():
        raise InvalidOperation
    return number
