"""Order schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class OrderStatus(str, Enum):
    """Order status enum."""

    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    PRINTING = "printing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderItemResponse(BaseModel):
    """Order item in response."""

    id: UUID
    product_slug: str
    product_name: str
    variant: str | None
    quantity: int
    unit_price: float
    pod_provider: str | None
    pod_status: str | None
    pod_tracking_number: str | None
    pod_tracking_url: str | None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response."""

    id: UUID
    status: str
    shipping_name: str | None
    shipping_email: str | None
    shipping_city: str | None
    shipping_country: str | None
    subtotal: float | None
    shipping_cost: float | None
    tax: float | None
    total: float | None
    currency: str
    items: list[OrderItemResponse]
    created_at: datetime
    paid_at: datetime | None
    shipped_at: datetime | None

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    """Request to create checkout session."""

    cart_id: UUID
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    checkout_url: str
    session_id: str
