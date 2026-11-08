"""Huellas para que reimportar un CSV de ventas no duplique (lógica pura).

- Archivo: sha256 del contenido. Si ya se importó en el negocio, se avisa antes de reimportar.
- Fila: sha256 de producto|fecha|cantidad|precio|n, donde n es cuántas veces apareció antes esa
  misma fila en el archivo. Así el mismo archivo es idempotente, pero tres ventas iguales el mismo
  día (legítimas) generan tres huellas distintas y entran las tres.

El formato del texto debe coincidir con el backfill de `db/migrations/005_sales_dedup.sql`.
"""
import hashlib
from collections import Counter
from datetime import date
from decimal import Decimal
from uuid import UUID

_CENTS = Decimal("0.01")


def file_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def row_key(product_id: UUID, sale_date: date, quantity: int, unit_price: Decimal) -> str:
    return f"{product_id}|{sale_date.isoformat()}|{quantity}|{Decimal(unit_price).quantize(_CENTS)}"


def row_hashes(keys: list[str]) -> list[str]:
    """Una huella por fila, en el mismo orden, numerando las repeticiones dentro del archivo."""
    seen: Counter[str] = Counter()
    hashes = []
    for key in keys:
        hashes.append(hashlib.sha256(f"{key}|{seen[key]}".encode("utf-8")).hexdigest())
        seen[key] += 1
    return hashes
