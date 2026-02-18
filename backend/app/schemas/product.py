"""Product schemas."""

from pydantic import BaseModel


class ProductVariant(BaseModel):
    """Product variant information."""

    name: str
    sku: str
    provider: str
    price: float


class Product(BaseModel):
    """Product for display in storefront."""

    slug: str
    name: str
    description: str
    category: str
    product_type: str  # sticker, shirt, print
    tags: list[str] = []
    image_url: str
    base_price: float
    variants: list[ProductVariant] = []
    is_active: bool = True

    class Config:
        from_attributes = True
