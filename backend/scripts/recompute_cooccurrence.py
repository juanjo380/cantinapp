"""Recalcula las co-ocurrencias de picos de venta. Pensado para tarea programada
(p. ej. Render Cron Job, una vez al día).  Uso (desde /backend):
    python -m scripts.recompute_cooccurrence                 # todos los negocios con ventas
    python -m scripts.recompute_cooccurrence --business-id <uuid>
"""
import argparse
import asyncio
from uuid import UUID

from sqlalchemy import text

from app.core.exceptions import UnprocessableError
from app.modules.recommendations.application.facade import run_cooccurrence_job
from app.shared.infrastructure.database import SessionFactory, engine


async def main(business_id: UUID | None) -> None:
    if business_id:
        business_ids = [business_id]
    else:
        async with SessionFactory() as session:
            business_ids = list((await session.execute(text("SELECT DISTINCT business_id FROM sales"))).scalars())

    for bid in business_ids:
        try:
            print(f"{bid}: {await run_cooccurrence_job(bid)} pares")
        except UnprocessableError as exc:
            print(f"{bid}: omitido ({exc})")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-id", type=UUID)
    asyncio.run(main(parser.parse_args().business_id))
