"""Designs API endpoints."""

import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image

from app.config import get_settings
from app.schemas.design import Design
from app.services.design_service import DesignService

router = APIRouter()
design_service = DesignService()
settings = get_settings()

# Mockup template configs: product_type → (template path, design bounding box)
MOCKUP_TEMPLATES = {
    "shirt": {
        "template": "shirt-template.png",
        "design_box": (275, 300, 250, 250),  # x, y, w, h on 800x800 canvas
    },
    "sticker": {
        "template": "sticker-template.png",
        "design_box": (130, 130, 540, 540),
    },
    "print": {
        "template": "print-template.png",
        "design_box": (160, 160, 480, 480),
    },
}

# Cache generated mockups in memory: (slug, product_type) → PNG bytes
_mockup_cache: dict[tuple[str, str], bytes] = {}


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


@router.get("/{slug}/mockup")
async def get_design_mockup(slug: str, type: str = "shirt"):
    """Serve the design composited onto a product mockup template.

    Composites the design image onto a product template (shirt, sticker, print)
    using Pillow. Result is cached in memory for fast subsequent requests.

    Query params:
        type: Product type — "shirt", "sticker", or "print" (default: shirt)
    """
    cache_key = (slug, type)
    if cache_key in _mockup_cache:
        return StreamingResponse(
            io.BytesIO(_mockup_cache[cache_key]),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    template_config = MOCKUP_TEMPLATES.get(type)
    if not template_config:
        raise HTTPException(status_code=400, detail=f"Unknown product type: {type}")

    # Load design image
    image_path = await design_service.get_design_image_path(slug)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Design image not found")

    # Load template image from frontend/public/mockups/
    template_dir = Path(__file__).resolve().parents[3] / "frontend" / "public" / "mockups"
    template_path = template_dir / template_config["template"]

    # Fallback: check if templates are mounted at /app/frontend/public/mockups/
    if not template_path.exists():
        template_path = Path("/app/mockups") / template_config["template"]
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Mockup template not found")

    # Composite design onto product template
    canvas = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
    design_img = Image.open(image_path).convert("RGBA")
    template_img = Image.open(str(template_path)).convert("RGBA")

    # Scale design to fit bounding box while maintaining aspect ratio
    bx, by, bw, bh = template_config["design_box"]
    scale = min(bw / design_img.width, bh / design_img.height)
    dw = int(design_img.width * scale)
    dh = int(design_img.height * scale)
    dx = bx + (bw - dw) // 2
    dy = by + (bh - dh) // 2

    design_resized = design_img.resize((dw, dh), Image.LANCZOS)

    # Draw design first (underneath), then template on top
    canvas.paste(design_resized, (dx, dy), design_resized)
    canvas.paste(template_img, (0, 0), template_img)

    # Export to PNG bytes
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    png_bytes = buf.getvalue()

    # Cache the result
    _mockup_cache[cache_key] = png_bytes

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
