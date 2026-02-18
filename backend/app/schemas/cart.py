"""Cart schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CartItemCreate(BaseModel):
    """Request to add item to cart."""

    product_slug: str
    product_name: str
    variant: str | None = None
    quantity: int = 1
    unit_price: float


class CartItemUpdate(BaseModel):
    """Request to update cart item."""

    quantity: int


class CartItemResponse(BaseModel):
    """Cart item in response."""

    id: UUID
    product_slug: str
    product_name: str
    variant: str | None
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class CartCreate(BaseModel):
    """Request to create a new cart."""

    pass


class CartResponse(BaseModel):
    """Cart response."""

    id: UUID
    items: list[CartItemResponse]
    item_count: int
    subtotal: float
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
