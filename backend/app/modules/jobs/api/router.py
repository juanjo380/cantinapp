"""Endpoint interno del trabajo diario. Lo llama GitHub Actions una vez al día; esa llamada
también despierta el servicio de Render (plan gratis). No usa JWT: se protege con X-Cron-Secret."""
import hmac

from fastapi import APIRouter, Header
from pydantic import SecretStr

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.modules.jobs.application.daily import run_daily_jobs

router = APIRouter(prefix="/api/internal/jobs", tags=["internal"])


def verify_cron_secret(provided: str | None, expected: SecretStr | None) -> None:
    if not provided:
        raise UnauthorizedError("Falta el header X-Cron-Secret")
    # Sin CRON_SECRET configurado (solo posible en development) el endpoint queda cerrado.
    if expected is None or not hmac.compare_digest(
        provided.encode("utf-8"), expected.get_secret_value().encode("utf-8")
    ):
        raise ForbiddenError("Secreto inválido")


@router.post("/daily", include_in_schema=False)
async def daily(x_cron_secret: str | None = Header(default=None)):
    verify_cron_secret(x_cron_secret, get_settings().cron_secret)
    results = await run_daily_jobs()
    return {
        "businesses": len(results),
        "failed": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
