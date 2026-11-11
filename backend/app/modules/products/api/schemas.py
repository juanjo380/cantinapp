"""Esquemas HTTP del módulo de productos (7 campos de HU02)."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=120)
    price: Decimal = Field(ge=0)
    quantity: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    supplier: str | None = Field(default=None, max_length=120)
    price: Decimal | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None  # reactivar un producto desactivado


class ProductOut(BaseModel):
    id: UUID
    name: str
    category: str | None
    supplier: str | None
    price: Decimal
    stock_quantity: int
    min_stock: int
    lead_time_days: int
    is_active: bool


class ComponentIn(BaseModel):
    component_id: UUID
    quantity: int = Field(ge=1, le=10_000)


class RecipeIn(BaseModel):
    components: list[ComponentIn] = Field(max_length=50)  # vacía = deja de ser compuesto

    @field_validator("components")
    @classmethod
    def _unique(cls, value):
        if len({c.component_id for c in value}) != len(value):
            raise ValueError("Hay componentes repetidos")
        return value


class ComponentOut(BaseModel):
    component_id: UUID
    name: str
    quantity: int
    stock_quantity: int


class CompositeOut(BaseModel):
    product_id: UUID
    name: str
    price: Decimal
    available: int  # unidades que se pueden armar con el stock actual
    components: list[ComponentOut]


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    limit: int
    offset: int


class ProductImportErrorOut(BaseModel):
    row: int
    field: str
    message: str


class ProductImportOut(BaseModel):
    file_name: str
    total_rows: int
    imported_rows: int
    error_rows: int
    status: str
    errors: list[ProductImportErrorOut] = []
