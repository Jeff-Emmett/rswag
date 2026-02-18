"""Design upload API — users upload their own artwork."""

import io
import re
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from app.config import get_settings
from app.api.designs import design_service

router = APIRouter()
settings = get_settings()

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_DIMENSION = 500


class UploadResponse(BaseModel):
    slug: str
    name: str
    image_url: str
    status: str
    products: list[dict]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


@router.post("/upload", response_model=UploadResponse)
async def upload_design(
    file: UploadFile,
    name: str = Form(...),
    space: str = Form("default"),
    tags: str = Form(""),
):
    """Upload a custom design image."""

    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only PNG, JPEG, and WebP files are accepted")

    # Read file and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "File size must be under 10 MB")

    # Open with Pillow and validate dimensions
    try:
        img = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(400, "Could not read image file")

    if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
        raise HTTPException(400, f"Image must be at least {MIN_DIMENSION}x{MIN_DIMENSION} pixels")

    # Create slug
    slug = slugify(name)
    if not slug:
        slug = f"upload-{uuid.uuid4().hex[:8]}"

    # Check for existing design
    design_dir = settings.designs_dir / "uploads" / slug
    if design_dir.exists():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        design_dir = settings.designs_dir / "uploads" / slug

    # Save image as PNG
    design_dir.mkdir(parents=True, exist_ok=True)
    img = img.convert("RGBA")
    image_path = design_dir / f"{slug}.png"
    img.save(str(image_path), "PNG")

    # Build metadata
    safe_name = name.replace('"', '\\"')
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else ["custom", "upload"]
    tags_str = ", ".join(tag_list)
    space_field = space if space != "default" else "all"

    metadata_content = f"""name: "{safe_name}"
slug: {slug}
description: "Custom uploaded design"
tags: [{tags_str}]
space: {space_field}
category: uploads
created: "{date.today().isoformat()}"
author: user-upload

source:
  file: {slug}.png
  format: png
  dimensions:
    width: {img.width}
    height: {img.height}
  dpi: 300
  color_profile: sRGB

products:
  - type: sticker
    provider: prodigi
    sku: GLOBAL-STI-KIS-3X3
    variants: [matte, gloss]
    retail_price: 3.50
  - type: shirt
    provider: printful
    sku: "71"
    variants: [S, M, L, XL, 2XL]
    retail_price: 29.99
  - type: print
    provider: prodigi
    sku: GLOBAL-FAP-A4
    variants: [matte, lustre]
    retail_price: 12.99

status: draft
"""
    metadata_path = design_dir / "metadata.yaml"
    metadata_path.write_text(metadata_content)

    # Clear design cache so the new upload is discoverable
    design_service.clear_cache()

    products = [
        {"type": "sticker", "price": 3.50},
        {"type": "shirt", "price": 29.99},
        {"type": "print", "price": 12.99},
    ]

    return UploadResponse(
        slug=slug,
        name=name,
        image_url=f"/api/designs/{slug}/image",
        status="draft",
        products=products,
    )
