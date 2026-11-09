"""Genera los CSV de prueba de tres negocios para evaluar la predicción (solo librería estándar).

Uso (desde cualquier carpeta):
    python docs/datos-prueba/generar_datos.py                 # termina ayer
    python docs/datos-prueba/generar_datos.py --end 2026-11-07

Las ventas deben terminar ayer: si se cargan semanas después, los últimos días quedan en 0 y la
predicción (que mira hasta hoy) cree que el negocio dejó de vender. En ese caso, regenera.
Semilla fija: mismas fechas = mismos archivos.

Cada negocio tiene un patrón distinto para que gane un modelo distinto (ver README.md):
  negocio1  Cantina escolar   cierra fines de semana y en la semana de receso  -> SEASONAL_WEEKLY
  negocio2  Tienda de barrio  fines de semana, quincena, un producto en alza    -> SEASONAL_WEEKLY / LINEAR
  negocio3  Cafetería          estable, un producto a la baja                   -> MOVING_AVERAGE / LINEAR
  negocio4  Droguería          400 días con fechas especiales (San Valentín, Amor y Amistad,
                               Navidad, fin de año): Postday, preservativos, chocolates y
                               Alka-Seltzer se disparan -> sección «Fechas especiales»
Los tres comparten productos (Gaseosa 400 ml, Agua 600 ml, Papas fritas) para comparar el mismo
artículo bajo patrones diferentes.
"""
import argparse
import random
from datetime import date, timedelta
from pathlib import Path

DAYS = 120
OUT = Path(__file__).resolve().parent

# Factor por día de la semana (lunes..domingo)
CANTINA = (1.0, 1.0, 1.05, 1.0, 1.2, 0.0, 0.0)
TIENDA = (0.85, 0.85, 0.9, 0.95, 1.2, 1.4, 1.1)
CAFE = (1.1, 1.0, 1.0, 1.0, 1.05, 0.9, 0.7)
DROGUERIA = (0.95, 0.95, 0.95, 1.0, 1.1, 1.2, 0.9)


def _third_saturday_september(year: int) -> date:
    first = date(year, 9, 1)
    return first + timedelta(days=(5 - first.weekday()) % 7 + 14)


# Fechas especiales de la droguería: (fecha según el año, [(producto, días desde la fecha, factor)]).
# La Postday sube DESPUÉS de la fecha: es el pico que nadie anticipa.
PICOS_DROGUERIA = [
    (lambda y: date(y, 2, 14), [
        ("Preservativos x3", -1, 4), ("Preservativos x3", 0, 5),
        ("Chocolates caja", -1, 5), ("Chocolates caja", 0, 6),
        ("Postday", 1, 12), ("Postday", 2, 9),
    ]),
    (_third_saturday_september, [
        ("Preservativos x3", -1, 3), ("Preservativos x3", 0, 4),
        ("Chocolates caja", 0, 3), ("Postday", 1, 6), ("Postday", 2, 4),
    ]),
    (lambda y: date(y, 12, 24), [("Chocolates caja", -1, 3), ("Alka-Seltzer x2", 1, 3)]),
    (lambda y: date(y, 12, 31), [
        ("Preservativos x3", 0, 3), ("Alka-Seltzer x2", 1, 6), ("Suero oral", 1, 3),
        ("Postday", 1, 5), ("Postday", 2, 3),
    ]),
]


def _special_days(first: date, last: date) -> dict[tuple[str, date], float]:
    factors = {}
    for year in range(first.year, last.year + 1):
        for rule, effects in PICOS_DROGUERIA:
            for product, offset, factor in effects:
                factors[(product, rule(year) + timedelta(days=offset))] = factor
    return factors

# (nombre, precio, categoría, proveedor, stock, mínimo, días abastecimiento, unidades/día, opciones)
# opciones: trend = cambio diario (0.008 = +0,8 %/día), prob = probabilidad de vender ese día (intermitente)
NEGOCIOS = {
    "negocio1": {
        "perfil": CANTINA,
        "receso": (date(2026, 10, 5), date(2026, 10, 9)),  # semana de receso escolar: todo en 0
        "quincena": 1.0,
        "evento": ("Empanada", "Gaseosa 400 ml"),  # día del jean: picos de empanada, al otro día más gaseosa
        "productos": [
            ("Empanada", 2500, "Comidas", "Panadería La Espiga", 40, 30, 1, 35, {}),
            ("Pastel de pollo", 3000, "Comidas", "Panadería La Espiga", 15, 20, 1, 18, {}),
            ("Arepa con queso", 2800, "Comidas", "Panadería La Espiga", 30, 10, 1, 12, {}),
            ("Gaseosa 400 ml", 3000, "Bebidas", "Distribuidora Central", 48, 24, 3, 22, {}),
            ("Agua 600 ml", 2000, "Bebidas", "Distribuidora Central", 36, 12, 3, 14, {}),
            ("Jugo en caja", 2200, "Bebidas", "Distribuidora Central", 8, 20, 3, 16, {}),
            ("Papas fritas", 2500, "Paquetes", "Snacks S.A.", 0, 15, 5, 10, {}),
            ("Chocolatina", 1200, "Dulces", "Dulces La Fe", 80, 20, 5, 20, {}),
            ("Galletas de avena", 1800, "Paquetes", "Snacks S.A.", 40, 10, 5, 8, {}),
            ("Yogur", 2600, "Lácteos", "Lácteos Andinos", 20, 10, 2, 6, {}),
        ],
    },
    "negocio2": {
        "perfil": TIENDA,
        "receso": None,
        "quincena": 1.5,
        "evento": ("Cerveza lata", "Agua 600 ml"),  # partidos: picos de cerveza, al otro día más agua
        "productos": [
            ("Arroz 1 kg", 4200, "Granos", "Mayorista El Sol", 60, 20, 4, 14, {}),
            ("Aceite 1 L", 9800, "Abarrotes", "Mayorista El Sol", 10, 12, 4, 5, {}),
            ("Huevos x30", 16500, "Lácteos y huevos", "Avícola Santa Ana", 12, 6, 2, 4, {}),
            ("Leche 1 L", 4300, "Lácteos y huevos", "Lácteos Andinos", 40, 20, 2, 18, {}),
            ("Pan tajado", 5200, "Panadería", "Panadería La Espiga", 15, 8, 1, 7, {}),
            ("Gaseosa 1,5 L", 6500, "Bebidas", "Distribuidora Central", 20, 15, 3, 4, {"trend": 0.008}),
            ("Gaseosa 400 ml", 3000, "Bebidas", "Distribuidora Central", 48, 24, 3, 12, {}),
            ("Agua 600 ml", 2000, "Bebidas", "Distribuidora Central", 30, 12, 3, 8, {}),
            ("Cerveza lata", 3500, "Bebidas", "Distribuidora Central", 72, 24, 3, 16, {}),
            ("Papas fritas", 2500, "Paquetes", "Snacks S.A.", 30, 10, 5, 6, {}),
            ("Pila AA", 2500, "Hogar", "Ferretería Central", 6, 4, 10, 1.5, {"prob": 0.25}),
        ],
    },
    "negocio3": {
        "perfil": CAFE,
        "receso": None,
        "quincena": 1.0,
        "evento": ("Pandebono", "Café con leche"),  # promo de pandebono, al otro día más café con leche
        "productos": [
            ("Café tinto", 1800, "Bebidas calientes", "Café del Valle", 300, 80, 7, 40, {}),
            ("Café con leche", 3200, "Bebidas calientes", "Café del Valle", 200, 60, 7, 25, {}),
            ("Chocolate caliente", 3500, "Bebidas calientes", "Café del Valle", 60, 20, 7, 14, {"trend": -0.006}),
            ("Pandebono", 2000, "Panadería", "Panadería La Espiga", 40, 25, 1, 30, {}),
            ("Croissant", 4500, "Panadería", "Panadería La Espiga", 10, 12, 1, 9, {}),
            ("Torta porción", 6000, "Postres", "Repostería Dulce Hogar", 12, 6, 2, 6, {}),
            ("Torta de cumpleaños", 45000, "Postres", "Repostería Dulce Hogar", 2, 1, 3, 1, {"prob": 0.12}),
            ("Gaseosa 400 ml", 3500, "Bebidas", "Distribuidora Central", 24, 12, 3, 6, {}),
            ("Agua 600 ml", 2500, "Bebidas", "Distribuidora Central", 24, 10, 3, 7, {}),
        ],
    },
    "negocio4": {
        "perfil": DROGUERIA,
        "dias": 400,  # más de un año: hace falta un San Valentín anterior para anticipar el próximo
        "receso": None,
        "quincena": 1.2,
        "evento": None,
        "fechas": True,
        "productos": [
            ("Acetaminofén 500 mg x10", 3500, "Analgésicos", "Distribuidora Pharma", 40, 15, 3, 8, {}),
            ("Ibuprofeno 400 mg x10", 5200, "Analgésicos", "Distribuidora Pharma", 25, 10, 3, 5, {}),
            ("Loratadina x10", 4000, "Antialérgicos", "Distribuidora Pharma", 15, 6, 3, 2, {}),
            ("Suero oral", 4800, "Hidratación", "Distribuidora Pharma", 20, 8, 3, 4, {}),
            ("Alka-Seltzer x2", 2500, "Digestivos", "Distribuidora Pharma", 30, 10, 3, 3, {}),
            ("Vitamina C x12", 8000, "Vitaminas", "Distribuidora Pharma", 20, 8, 5, 2.5, {}),
            ("Preservativos x3", 9500, "Salud sexual", "Distribuidora Pharma", 18, 10, 5, 3, {}),
            ("Postday", 18000, "Salud sexual", "Distribuidora Pharma", 6, 4, 5, 0.8, {}),
            ("Prueba de embarazo", 9000, "Salud sexual", "Distribuidora Pharma", 8, 4, 5, 0.8, {}),
            ("Toallas higiénicas x10", 6500, "Cuidado personal", "Distribuidora Pharma", 30, 10, 4, 4, {}),
            ("Chocolates caja", 15000, "Confitería", "Dulces La Fe", 10, 5, 5, 1.5, {}),
            ("Agua 600 ml", 2500, "Bebidas", "Distribuidora Central", 30, 10, 3, 6, {}),
        ],
    },
}


def _is_payday(day: date) -> bool:
    return day.day in (15, 16, 1) or (day + timedelta(days=1)).month != day.month


def _money(value: int) -> str:
    return str(value)


def generate(end: date) -> None:
    for key, negocio in NEGOCIOS.items():
        days = negocio.get("dias", DAYS)
        first = end - timedelta(days=days - 1)
        rng = random.Random(f"cantinapp-{key}")
        trigger, follower = negocio["evento"] or (None, None)
        events = set()
        if trigger:
            open_days = [first + timedelta(days=i) for i in range(days)
                         if negocio["perfil"][(first + timedelta(days=i)).weekday()] > 0]
            events = set(rng.sample(open_days[14:-2], 8))  # tras 14 días hay base para medir el pico
        special = _special_days(first, end) if negocio.get("fechas") else {}

        rows = []
        for offset in range(days):
            day = first + timedelta(days=offset)
            factor = negocio["perfil"][day.weekday()]
            if negocio["receso"] and negocio["receso"][0] <= day <= negocio["receso"][1]:
                factor = 0.0
            if _is_payday(day):
                factor *= negocio["quincena"]
            if factor == 0:
                continue
            for name, price, *_rest, daily, opts in negocio["productos"]:
                if rng.random() > opts.get("prob", 1.0):
                    continue
                units = daily * factor * (1 + opts.get("trend", 0.0)) ** offset * rng.gauss(1.0, 0.18)
                if name == trigger and day in events:
                    units *= 3
                if name == follower and day - timedelta(days=1) in events:
                    units *= 2
                units *= special.get((name, day), 1)
                quantity = max(1, round(units)) if opts.get("prob") else round(units)
                if quantity > 0:
                    rows.append(f"{name};{day:%d/%m/%Y};{quantity};{_money(price)}")

        products = [
            f"{name};{_money(price)};{category};{supplier};{stock};{minimum};{lead}"
            for name, price, category, supplier, stock, minimum, lead, _daily, _opts in negocio["productos"]
        ]
        _write(OUT / f"{key}Productos.csv",
               "nombre;precio;categoria;proveedor;stock_inicial;stock_minimo;dias_abastecimiento", products)
        _write(OUT / f"{key}Ventas.csv", "producto;fecha;cantidad;precio", rows)
        print(f"{key}: {len(products)} productos, {len(rows)} ventas ({first:%d/%m/%Y} a {end:%d/%m/%Y})")


def _write(path: Path, header: str, lines: list[str]) -> None:
    # UTF-8 con BOM y ';': Excel en español lo abre con tildes y columnas bien, igual que las plantillas.
    path.write_text("﻿" + "\r\n".join([header, *lines]) + "\r\n", encoding="utf-8", newline="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1))
    generate(parser.parse_args().end)
