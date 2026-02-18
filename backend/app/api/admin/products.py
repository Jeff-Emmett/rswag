"""Admin product management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.design_service import DesignService
from app.services.auth_service import get_current_admin

router = APIRouter()


class ProductOverrideRequest(BaseModel):
    is_active: bool | None = None
    price_override: float | None = None


def get_design_service() -> DesignService:
    return DesignService()


@router.put("/{slug}/override")
async def update_product_override(
    slug: str,
    override: ProductOverrideRequest,
    db: AsyncSession = Depends(get_db),
    design_service: DesignService = Depends(get_design_service),
    _admin=Depends(get_current_admin),
):
    """Update product visibility or price override (admin only)."""
    # Verify product exists
    product = await design_service.get_product(slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update override in database
    await design_service.set_product_override(
        db=db,
        slug=slug,
        is_active=override.is_active,
        price_override=override.price_override,
    )

    return {"status": "updated", "slug": slug}


@router.post("/sync")
async def sync_designs(
    design_service: DesignService = Depends(get_design_service),
    _admin=Depends(get_current_admin),
):
    """Force sync designs from the designs directory (admin only)."""
    # Clear any caches and reload
    design_service.clear_cache()
    designs = await design_service.list_designs()
    return {"status": "synced", "count": len(designs)}
