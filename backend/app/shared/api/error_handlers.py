"""Traduce excepciones a respuestas HTTP (RNF-06)."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import AppError

logger = logging.getLogger("cantinapp")

_UNIQUE_VIOLATION = "23505"
_FOREIGN_KEY_VIOLATION = "23503"
_CHECK_VIOLATION = "23514"


def _sqlstate(exc: IntegrityError) -> str | None:
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(IntegrityError)
    async def _handle_integrity(_: Request, exc: IntegrityError) -> JSONResponse:
        state = _sqlstate(exc)
        if state == _UNIQUE_VIOLATION:
            return JSONResponse(status_code=409, content={"detail": "El recurso ya existe"})
        if state == _CHECK_VIOLATION:
            return JSONResponse(
                status_code=422, content={"detail": "La operación deja el inventario en negativo"}
            )
        if state == _FOREIGN_KEY_VIOLATION:
            return JSONResponse(status_code=404, content={"detail": "Referencia inexistente"})
        logger.warning("IntegrityError no mapeado: %s", exc)
        return JSONResponse(status_code=409, content={"detail": "Violación de integridad"})

    @app.exception_handler(SQLAlchemyError)
    async def _handle_db_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Error de base de datos", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Error de base de datos"})
