"""Trabajo diario (alertas, co-ocurrencias y correo-resumen) para quien tenga cron propio.
Equivale a POST /api/internal/jobs/daily. Uso (desde /backend):
    python -m scripts.run_daily_jobs                  # todos los negocios
    python -m scripts.run_daily_jobs --business-id <uuid>
Sale con código 1 si algún negocio falló (para que el cron lo marque).
"""
import argparse
import asyncio
import logging
import sys
from uuid import UUID

from app.modules.jobs.application.daily import run_daily_jobs
from app.shared.infrastructure.database import engine


async def main(business_id: UUID | None) -> int:
    try:
        results = await run_daily_jobs([business_id] if business_id else None)
    finally:
        await engine.dispose()
    for result in results:
        print(result)
    return 1 if any(not r["ok"] for r in results) else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-id", type=UUID)
    sys.exit(asyncio.run(main(parser.parse_args().business_id)))
