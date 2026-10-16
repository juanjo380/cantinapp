"""Prueba rapida de conexion y esquema.  Uso (desde /backend):
    python -m scripts.check_db
"""
import asyncio

from sqlalchemy import text

from app.infrastructure.database import engine

EXPECTED = {
    "businesses", "users", "categories", "suppliers", "products", "sales_imports", "sales",
    "inventory_movements", "forecasts", "recommendations", "alerts",
}


async def main() -> None:
    async with engine.connect() as conn:
        version = (await conn.execute(text("SELECT version()"))).scalar_one()
        print("Conexion OK ->", version.split(",")[0])
        rows = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        found = {r[0] for r in rows}
        missing = EXPECTED - found
        print("Esquema completo" if not missing else f"Faltan tablas: {sorted(missing)}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())