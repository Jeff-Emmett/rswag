"""Cart API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.cart import (
    CartCreate,
    CartResponse,
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
)
from app.services.cart_service import CartService

router = APIRouter()


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(db)


@router.post("", response_model=CartResponse)
async def create_cart(
    service: CartService = Depends(get_cart_service),
):
    """Create a new shopping cart."""
    cart = await service.create_cart()
    return cart


@router.get("/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: UUID,
    service: CartService = Depends(get_cart_service),
):
    """Get cart by ID."""
    cart = await service.get_cart(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@router.post("/{cart_id}/items", response_model=CartResponse)
async def add_item(
    cart_id: UUID,
    item: CartItemCreate,
    service: CartService = Depends(get_cart_service),
):
    """Add item to cart."""
    cart = await service.add_item(cart_id, item)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@router.put("/{cart_id}/items/{item_id}", response_model=CartResponse)
async def update_item(
    cart_id: UUID,
    item_id: UUID,
    update: CartItemUpdate,
    service: CartService = Depends(get_cart_service),
):
    """Update cart item quantity."""
    cart = await service.update_item(cart_id, item_id, update.quantity)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart


@router.delete("/{cart_id}/items/{item_id}", response_model=CartResponse)
async def remove_item(
    cart_id: UUID,
    item_id: UUID,
    service: CartService = Depends(get_cart_service),
):
    """Remove item from cart."""
    cart = await service.remove_item(cart_id, item_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart or item not found")
    return cart
