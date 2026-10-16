"""Capa de infraestructura: conexion directa a Supabase (PostgreSQL) con
SQLAlchemy 2.0 asincrono + asyncpg."""
from collections.abc import AsyncGenerator
from uuid import uuid4

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings


def build_database_url(settings: Settings) -> URL:
    # URL.create escapa automaticamente usuario/password con caracteres especiales
    return URL.create(
        drivername="postgresql+asyncpg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )


def create_engine(settings: Settings) -> AsyncEngine:
    connect_args: dict = {}
    if settings.db_ssl:
        connect_args["ssl"] = "require"  # Supabase exige conexiones cifradas

    kwargs: dict = {"echo": settings.db_echo, "pool_pre_ping": True}

    if settings.db_use_transaction_pooler:
        # El Transaction pooler (pgbouncer, puerto 6543) no soporta prepared
        # statements ni pools persistentes del lado de la app.
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0
        connect_args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid4()}__"
        kwargs["poolclass"] = NullPool
    else:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
        kwargs["pool_recycle"] = 1800

    return create_async_engine(build_database_url(settings), connect_args=connect_args, **kwargs)


engine: AsyncEngine = create_engine(get_settings())

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: una sesion por request.

    No hace commit automatico: los handlers (capa Application) deciden cuando
    confirmar la transaccion con `await session.commit()`. Si ocurre una
    excepcion, la transaccion se revierte al cerrar la sesion.
    """
    async with SessionFactory() as session:
        yield session