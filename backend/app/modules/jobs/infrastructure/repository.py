"""Consultas del trabajo diario: negocios a procesar y a quién avisar."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlJobsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def business_ids(self) -> list[UUID]:
        """Negocios con al menos un producto activo (sin productos no hay alertas que generar)."""
        rows = await self.session.execute(text("SELECT DISTINCT business_id FROM products WHERE is_active"))
        return list(rows.scalars())

    async def digest_target(self, business_id: UUID) -> tuple[str, list[str]]:
        """(nombre del negocio, correos de dueño y administradores activos)."""
        name = (
            await self.session.execute(text("SELECT name FROM businesses WHERE id = :id"), {"id": business_id})
        ).scalar_one()
        emails = (
            await self.session.execute(
                text(
                    "SELECT u.email FROM business_members m JOIN users u ON u.id = m.user_id "
                    "WHERE m.business_id = :id AND m.role IN ('OWNER', 'ADMIN') AND u.is_active ORDER BY u.email"
                ),
                {"id": business_id},
            )
        ).scalars()
        return name, list(emails)
