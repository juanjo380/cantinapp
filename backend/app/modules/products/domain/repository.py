"""Puerto del repositorio de productos."""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.products.domain.entities import Product


class ProductRepository(Protocol):
    async def list(
        self,
        business_id: UUID,
        *,
        search: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        sort: str = "name",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Product], int]: ...

    async def get(self, business_id: UUID, product_id: UUID) -> Product | None: ...

    async def get_by_name(self, business_id: UUID, name: str) -> Product | None: ...

    async def add(
        self,
        *,
        business_id: UUID,
        name: str,
        category: str | None,
        supplier: str | None,
        price: Decimal,
        quantity: int,
        min_stock: int,
        lead_time_days: int,
    ) -> Product: ...

    async def update(self, product: Product, changes: dict) -> Product: ...

    async def deactivate(self, product: Product) -> None: ...

    # Compuestos (recetas). `has_recipe` solo cuenta si el negocio tiene la sección activa.
    async def composites_enabled(self, business_id: UUID) -> bool: ...

    async def has_recipe(self, business_id: UUID, product_id: UUID) -> bool: ...

    async def list_composites(self, business_id: UUID) -> list[dict]: ...

    async def with_recipe(self, business_id: UUID, product_ids: list[UUID]) -> set[UUID]: ...

    async def used_as_component(self, business_id: UUID, product_id: UUID) -> bool: ...

    async def set_components(self, business_id: UUID, product_id: UUID, items: dict[UUID, int]) -> None: ...
