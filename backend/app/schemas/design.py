"""Design schemas."""

from pydantic import BaseModel


class DesignSource(BaseModel):
    """Design source file information."""

    file: str
    format: str
    dimensions: dict[str, int]
    dpi: int
    color_profile: str = "sRGB"


class DesignProduct(BaseModel):
    """Product configuration for a design."""

    type: str
    provider: str
    sku: str
    variants: list[str] = []
    retail_price: float


class Design(BaseModel):
    """Design information from metadata.yaml."""

    slug: str
    name: str
    description: str
    tags: list[str] = []
    category: str
    author: str = ""
    created: str = ""
    source: DesignSource
    products: list[DesignProduct] = []
    status: str = "draft"
    image_url: str = ""

    class Config:
        from_attributes = True
