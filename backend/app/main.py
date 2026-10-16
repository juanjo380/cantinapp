from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.alerts.api.router import router as alerts_router
from app.modules.analytics.api.router import router as analytics_router
from app.modules.auth.api.router import router as auth_router
from app.modules.dashboard.api.router import router as dashboard_router
from app.modules.forecasting.api.router import router as forecasting_router
from app.modules.inventory.api.router import router as inventory_router
from app.modules.products.api.router import router as products_router
from app.modules.recommendations.api.router import router as recommendations_router
from app.modules.sales.api.router import router as sales_router
from app.shared.api.error_handlers import register_error_handlers
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

for router in (
    auth_router,
    products_router,
    sales_router,
    inventory_router,
    analytics_router,
    forecasting_router,
    recommendations_router,
    dashboard_router,
    alerts_router,
):
    app.include_router(router)


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
