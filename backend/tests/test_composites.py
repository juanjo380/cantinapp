"""Compuestos: reglas de la receta y venta manual de un producto sin stock propio."""
import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import UnprocessableError
from app.modules.products.application.handlers import set_recipe
from app.modules.sales.application.commands import CreateSaleCommand
from app.modules.sales.application.handlers import register_sale

BID = uuid4()


class FakeProducts:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.items = {}
        self.recipes = {}

    def new(self, name, stock=0):
        product = SimpleNamespace(id=uuid4(), name=name, price=Decimal("1000"), stock_quantity=stock, is_active=True)
        self.items[product.id] = product
        return product

    async def composites_enabled(self, business_id):
        return self.enabled

    async def get(self, business_id, product_id):
        return self.items.get(product_id)

    async def has_recipe(self, business_id, product_id):
        return self.enabled and bool(self.recipes.get(product_id))

    async def used_as_component(self, business_id, product_id):
        return any(product_id in r for r in self.recipes.values())

    async def with_recipe(self, business_id, product_ids):
        return {p for p in product_ids if self.recipes.get(p)}

    async def set_components(self, business_id, product_id, items):
        self.recipes[product_id] = items


def test_recipe_rules():
    repo = FakeProducts()
    burger, bread, meat = repo.new("Hamburguesa"), repo.new("Pan", 5), repo.new("Carne", 5)
    asyncio.run(set_recipe(repo, BID, burger.id, {bread.id: 1, meat.id: 1}))
    assert repo.recipes[burger.id] == {bread.id: 1, meat.id: 1}

    combo = repo.new("Combo")
    for bad in ({combo.id: 1}, {burger.id: 1}):  # a sí mismo / componente que ya es compuesto
        with pytest.raises(UnprocessableError):
            asyncio.run(set_recipe(repo, BID, combo.id, bad))
    with pytest.raises(UnprocessableError):  # un componente no puede volverse compuesto
        asyncio.run(set_recipe(repo, BID, bread.id, {meat.id: 1}))
    with pytest.raises(UnprocessableError):
        asyncio.run(set_recipe(FakeProducts(enabled=False), BID, burger.id, {}))


def test_composite_sale_skips_own_stock_check():
    repo = FakeProducts()
    burger, bread = repo.new("Hamburguesa"), repo.new("Pan", 5)
    repo.recipes[burger.id] = {bread.id: 1}
    added = []

    class Sales:
        async def add(self, **kwargs):
            added.append(kwargs)

    command = CreateSaleCommand(
        business_id=BID, product_id=burger.id, sale_date=date(2026, 11, 11), quantity=2,
        unit_price=None, created_by=None, location_id=None,
    )
    asyncio.run(register_sale(Sales(), repo, command))  # el trigger descuenta el pan
    assert added[0]["quantity"] == 2

    repo.enabled = False  # sección apagada: vuelve a exigir stock propio
    with pytest.raises(UnprocessableError):
        asyncio.run(register_sale(Sales(), repo, command))
