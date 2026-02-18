"""Designs API endpoints."""

import io
import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image

from app.config import get_settings
from app.schemas.design import Design
from app.services.design_service import DesignService

logger = logging.getLogger(__name__)
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

# Map mockup type → matching product types from metadata
_TYPE_MAP = {
    "shirt": ("shirt", "tshirt", "tee", "hoodie"),
    "sticker": ("sticker",),
    "print": ("print",),
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
            "Cache-Control": "public, max-age=86400",
        },
    )


@router.get("/{slug}/mockup")
async def get_design_mockup(slug: str, type: str = "shirt"):
    """Serve the design composited onto a product mockup template.

    For Printful-provider designs: fetches photorealistic mockup from
    Printful's mockup generator API (cached after first generation).
    For other designs: composites with Pillow using local templates.

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

    # Load design to check provider
    design = await design_service.get_design(slug)
    if not design:
        raise HTTPException(status_code=404, detail="Design not found")

    # Find a Printful-provider product matching the requested mockup type
    printful_product = None
    accepted_types = _TYPE_MAP.get(type, (type,))
    for p in design.products:
        if p.provider == "printful" and p.type in accepted_types:
            printful_product = p
            break

    # Try Printful mockup API for Printful-provider designs
    if printful_product and settings.printful_api_token:
        png_bytes = await _get_printful_mockup(slug, printful_product)
        if png_bytes:
            _mockup_cache[cache_key] = png_bytes
            return StreamingResponse(
                io.BytesIO(png_bytes),
                media_type="image/png",
                headers={"Cache-Control": "public, max-age=86400"},
            )

    # Fallback: Pillow compositing with local templates
    return await _pillow_mockup(slug, type)


async def _get_printful_mockup(slug: str, product) -> bytes | None:
    """Fetch mockup from Printful API. Returns PNG bytes or None."""
    from app.pod.printful_client import PrintfulClient

    printful = PrintfulClient()
    if not printful.enabled:
        return None

    try:
        product_id = int(product.sku)

        # Get first variant for mockup preview
        variants = await printful.get_catalog_variants(product_id)
        if not variants:
            logger.warning(f"No Printful variants for product {product_id}")
            return None
        variant_ids = [variants[0]["id"]]

        # Public image URL for Printful to download
        image_url = f"https://fungiswag.jeffemmett.com/api/designs/{slug}/image"

        # Generate mockup (blocks up to ~60s on first call)
        mockups = await printful.generate_mockup_and_wait(
            product_id=product_id,
            variant_ids=variant_ids,
            image_url=image_url,
        )

        if not mockups:
            return None

        # Find a mockup URL from the result
        mockup_url = None
        for m in mockups:
            mockup_url = m.get("mockup_url") or m.get("url")
            if mockup_url:
                break

        if not mockup_url:
            logger.warning(f"No mockup URL in Printful response for {slug}")
            return None

        # Download the mockup image
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(mockup_url)
            resp.raise_for_status()
            return resp.content

    except Exception as e:
        logger.warning(f"Printful mockup failed for {slug}: {e}")
        return None


async def _pillow_mockup(slug: str, type: str) -> StreamingResponse:
    """Generate mockup using Pillow compositing with local templates."""
    template_config = MOCKUP_TEMPLATES.get(type)
    if not template_config:
        raise HTTPException(status_code=400, detail=f"Unknown product type: {type}")

    image_path = await design_service.get_design_image_path(slug)
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Design image not found")

    # Load template from frontend/public/mockups/ or /app/mockups/ (Docker mount)
    template_dir = Path(__file__).resolve().parents[3] / "frontend" / "public" / "mockups"
    template_path = template_dir / template_config["template"]
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
    cache_key = (slug, type)
    _mockup_cache[cache_key] = png_bytes

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
