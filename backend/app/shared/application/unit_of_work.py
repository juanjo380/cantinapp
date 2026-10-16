"""Puerto Unit of Work: agrupa la transacción de una operación."""
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Protocol):
    session: AsyncSession

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
