"""Spaces API endpoints."""

from fastapi import APIRouter, HTTPException

from app.services.space_service import SpaceService, Space

router = APIRouter()
space_service = SpaceService()


@router.get("", response_model=list[Space])
async def list_spaces():
    """List all available spaces."""
    return space_service.list_spaces()


@router.get("/{space_id}", response_model=Space)
async def get_space(space_id: str):
    """Get a specific space by ID."""
    space = space_service.get_space(space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space
