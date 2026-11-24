"""Puerto del repositorio de productos."""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.products.domain.discounts import ActiveDiscount, DiscountCandidate
from app.modules.products.domain.entities import Product


class ProductRepository(Protocol):
    async def list(
        self,
        business_id: UUID,
        *,
        search: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        composite: bool | None = None,
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
        is_composite: bool = False,
    ) -> Product: ...

    async def update(self, product: Product, changes: dict) -> Product: ...

    async def deactivate(self, product: Product) -> None: ...

    async def discount_candidates(self, business_id: UUID, *, days: int) -> list[DiscountCandidate]: ...

    async def active_discounts(self, business_id: UUID) -> list[ActiveDiscount]: ...

    async def list_price(self, product: Product) -> Decimal: ...

    async def apply_discount(self, product: Product, new_price: Decimal) -> Product: ...

    async def remove_discount(self, product: Product) -> Product | None: ...

    # Compuestos (products.is_composite + receta en product_components).
    async def composites_enabled(self, business_id: UUID) -> bool: ...

    async def list_composites(self, business_id: UUID) -> list[dict]: ...

    async def set_components(self, business_id: UUID, product_id: UUID, items: dict[UUID, int]) -> None: ...
