"""Products API endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.product import Product
from app.services.design_service import DesignService

router = APIRouter()
design_service = DesignService()


@router.get("", response_model=list[Product])
async def list_products(
    category: str | None = None,
    product_type: str | None = None,
    space: str | None = None,
):
    """List all products (designs with variants flattened for storefront)."""
    products = await design_service.list_products(
        category=category,
        product_type=product_type,
        space=space,
    )
    return products


@router.get("/{slug}", response_model=Product)
async def get_product(slug: str):
    """Get a single product by slug."""
    product = await design_service.get_product(slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
