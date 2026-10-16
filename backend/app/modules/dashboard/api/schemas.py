"""Esquemas HTTP del dashboard."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LowStockItemOut(BaseModel):
    product_id: UUID
    name: str
    stock_quantity: int
    min_stock: int
    status: str


class TrendPointOut(BaseModel):
    date: date
    units: int


class CurrentPeriodOut(BaseModel):
    units_sold: int
    revenue: Decimal


class DashboardOut(BaseModel):
    total_products: int
    total_stock: int
    inventory_value: Decimal
    current_period: CurrentPeriodOut
    low_stock_products: list[LowStockItemOut]
    trend: list[TrendPointOut]
