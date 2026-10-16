"""Implementación del Unit of Work sobre la sesión async de SQLAlchemy."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.database import get_db


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


async def get_uow(session: AsyncSession = Depends(get_db)) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session)
