"""Checkout API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import CheckoutRequest, CheckoutResponse
from app.services.stripe_service import StripeService
from app.services.cart_service import CartService

router = APIRouter()


def get_stripe_service() -> StripeService:
    return StripeService()


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(db)


@router.post("/session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    stripe_service: StripeService = Depends(get_stripe_service),
    cart_service: CartService = Depends(get_cart_service),
):
    """Create a Stripe checkout session."""
    # Get cart
    cart = await cart_service.get_cart(request.cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Create Stripe session
    result = await stripe_service.create_checkout_session(
        cart=cart,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )

    return CheckoutResponse(
        checkout_url=result["url"],
        session_id=result["session_id"],
    )
