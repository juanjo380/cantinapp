"""Compuestos: reglas de la receta y venta manual de un producto sin stock propio."""
import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, UnprocessableError
from app.modules.products.application.commands import CreateProductCommand
from app.modules.products.application.handlers import create_composite, set_recipe
from app.modules.sales.application.commands import CreateSaleCommand
from app.modules.sales.application.handlers import register_sale

BID = uuid4()


class FakeProducts:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.items = {}
        self.recipes = {}

    def new(self, name, stock=0, composite=False):
        product = SimpleNamespace(
            id=uuid4(), name=name, price=Decimal("1000"), stock_quantity=stock, is_active=True, is_composite=composite
        )
        self.items[product.id] = product
        return product

    async def composites_enabled(self, business_id):
        return self.enabled

    async def get(self, business_id, product_id):
        return self.items.get(product_id)

    async def add(self, *, name, price, is_composite=False, **_):
        product = self.new(name, composite=is_composite)
        product.price = price
        return product

    async def set_components(self, business_id, product_id, items):
        self.recipes[product_id] = items


def _command(name="Hamburguesa"):
    return CreateProductCommand(
        business_id=BID, name=name, price=Decimal("12000"), quantity=0, min_stock=0, lead_time_days=0
    )


def test_create_composite_with_recipe():
    repo = FakeProducts()
    bread, meat = repo.new("Pan", 5), repo.new("Carne", 5)
    burger = asyncio.run(create_composite(repo, _command(), {bread.id: 1, meat.id: 2}))
    assert burger.is_composite and burger.stock_quantity == 0
    assert repo.recipes[burger.id] == {bread.id: 1, meat.id: 2}
    with pytest.raises(UnprocessableError):  # sección apagada
        asyncio.run(create_composite(FakeProducts(enabled=False), _command(), {bread.id: 1}))


def test_recipe_rules():
    repo = FakeProducts()
    burger, bread, meat = repo.new("Hamburguesa", composite=True), repo.new("Pan", 5), repo.new("Carne", 5)
    asyncio.run(set_recipe(repo, BID, burger.id, {bread.id: 1, meat.id: 1}))
    assert repo.recipes[burger.id] == {bread.id: 1, meat.id: 1}

    combo = repo.new("Combo", composite=True)
    with pytest.raises(UnprocessableError):  # un compuesto no puede ser componente
        asyncio.run(set_recipe(repo, BID, combo.id, {burger.id: 1}))
    with pytest.raises(UnprocessableError):  # receta vacía
        asyncio.run(set_recipe(repo, BID, combo.id, {}))
    with pytest.raises(NotFoundError):  # un producto simple no lleva receta
        asyncio.run(set_recipe(repo, BID, bread.id, {meat.id: 1}))


def test_composite_sale_skips_own_stock_check():
    repo = FakeProducts()
    burger, bread = repo.new("Hamburguesa", composite=True), repo.new("Pan", 5)
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
