from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.shared.infrastructure.database import engine, get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Falla rapido al arrancar si la BD no es alcanzable
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        info = (await db.execute(text("SELECT current_database() AS db, version() AS version"))).one()
        tables = (
            await db.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
        ).scalar_one()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {exc.__class__.__name__}")
    return {"status": "ok", "database": info.db, "public_tables": tables, "server": info.version.split(",")[0]}