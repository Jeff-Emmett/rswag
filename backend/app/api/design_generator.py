"""AI design generation API."""

import os
import re
import uuid
from datetime import date
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.api.designs import design_service

router = APIRouter()
settings = get_settings()


class DesignRequest(BaseModel):
    """Request to generate a new design."""
    concept: str
    name: str
    tags: list[str] = []
    product_type: str = "sticker"


class DesignResponse(BaseModel):
    """Response with generated design info."""
    slug: str
    name: str
    image_url: str
    status: str


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


@router.post("/generate", response_model=DesignResponse)
async def generate_design(request: DesignRequest):
    """Generate a new design using AI."""

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI generation not configured. Set GEMINI_API_KEY."
        )

    # Create slug from name
    slug = slugify(request.name)
    if not slug:
        slug = f"design-{uuid.uuid4().hex[:8]}"

    # Check if design already exists
    design_dir = settings.designs_dir / "stickers" / slug
    if design_dir.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Design '{slug}' already exists"
        )

    # Build the image generation prompt
    style_prompt = f"""A striking sticker design for "{request.name}".
{request.concept}
The design should have a clean, modern spatial-web aesthetic with interconnected
nodes, network patterns, and a collaborative/commons feel.
Colors: vibrant cyan, warm orange accents on dark background.
High contrast, suitable for vinyl sticker printing.
Square format, clean edges for die-cut sticker."""

    # Call Gemini API for image generation
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Use gemini-3-pro-image-preview for image generation
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent?key={gemini_api_key}",
                json={
                    "contents": [{
                        "parts": [{
                            "text": style_prompt
                        }]
                    }],
                    "generationConfig": {
                        "responseModalities": ["image", "text"]
                    }
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "Unknown error"
                raise HTTPException(
                    status_code=502,
                    detail=f"AI generation failed ({response.status_code}): {error_detail}"
                )

            result = response.json()

            # Extract image data from response
            image_data = None
            for candidate in result.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        image_data = part["inlineData"]["data"]
                        break
                if image_data:
                    break

            if not image_data:
                # Log what we got for debugging
                import json
                raise HTTPException(
                    status_code=502,
                    detail=f"AI did not return an image. Response: {json.dumps(result)[:500]}"
                )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="AI generation timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI generation error: {str(e)}"
        )

    # Create design directory
    design_dir.mkdir(parents=True, exist_ok=True)

    # Save image
    import base64
    image_path = design_dir / f"{slug}.png"
    image_bytes = base64.b64decode(image_data)
    image_path.write_bytes(image_bytes)

    # Create metadata.yaml
    # Escape quotes in user-provided strings to prevent YAML parsing errors
    safe_name = request.name.replace('"', '\\"')
    safe_concept = request.concept.replace('"', '\\"')
    tags_str = ", ".join(request.tags) if request.tags else "rspace, sticker, ai-generated"
    metadata_content = f"""name: "{safe_name}"
slug: {slug}
description: "{safe_concept}"
tags: [{tags_str}]
created: {date.today().isoformat()}
author: ai-generated

source:
  file: {slug}.png
  format: png
  dimensions:
    width: 1024
    height: 1024
  dpi: 300
  color_profile: sRGB

products:
  - type: sticker
    provider: prodigi
    sku: GLOBAL-STI-KIS-3X3
    variants: [matte, gloss]
    retail_price: 3.50

status: draft
"""

    metadata_path = design_dir / "metadata.yaml"
    metadata_path.write_text(metadata_content)

    return DesignResponse(
        slug=slug,
        name=request.name,
        image_url=f"/api/designs/{slug}/image",
        status="draft"
    )


def find_design_dir(slug: str) -> Path | None:
    """Find a design directory by slug, searching all categories."""
    for category_dir in settings.designs_dir.iterdir():
        if not category_dir.is_dir():
            continue
        design_dir = category_dir / slug
        if design_dir.exists() and (design_dir / "metadata.yaml").exists():
            return design_dir
    return None


@router.post("/{slug}/activate")
async def activate_design(slug: str):
    """Activate a draft design to make it visible in the store."""

    design_dir = find_design_dir(slug)
    if not design_dir:
        raise HTTPException(status_code=404, detail="Design not found")

    metadata_path = design_dir / "metadata.yaml"

    # Read and update metadata
    content = metadata_path.read_text()
    content = content.replace("status: draft", "status: active")
    metadata_path.write_text(content)

    # Clear the design service cache so the new status is picked up
    design_service.clear_cache()

    return {"status": "activated", "slug": slug}


@router.delete("/{slug}")
async def delete_design(slug: str):
    """Delete a design (only drafts can be deleted)."""
    import shutil

    design_dir = find_design_dir(slug)
    if not design_dir:
        raise HTTPException(status_code=404, detail="Design not found")

    metadata_path = design_dir / "metadata.yaml"

    # Check if draft
    content = metadata_path.read_text()
    if "status: active" in content:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active designs. Set to draft first."
        )

    # Delete directory
    shutil.rmtree(design_dir)

    return {"status": "deleted", "slug": slug}
