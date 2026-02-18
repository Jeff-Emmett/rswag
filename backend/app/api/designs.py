"""Designs API endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.design import Design
from app.services.design_service import DesignService

router = APIRouter()
design_service = DesignService()


@router.get("", response_model=list[Design])
async def list_designs(
    status: str = "active",
    category: str | None = None,
    space: str | None = None,
):
    """List all designs."""
    designs = await design_service.list_designs(status=status, category=category, space=space)
    return designs


@router.get("/{slug}", response_model=Design)
async def get_design(slug: str):
    """Get a single design by slug."""
    design = await design_service.get_design(slug)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")
    return design


@router.get("/{slug}/image")
async def get_design_image(slug: str):
    """Serve the design image."""
    image_path = await design_service.get_design_image_path(slug)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        image_path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
        },
    )
