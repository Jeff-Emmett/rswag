"""Checkout API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import CheckoutRequest, CheckoutResponse
from app.services.mollie_service import MollieService
from app.services.cart_service import CartService

router = APIRouter()


def get_mollie_service() -> MollieService:
    return MollieService()


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(db)


@router.post("/session", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_request: CheckoutRequest,
    request: Request,
    mollie_service: MollieService = Depends(get_mollie_service),
    cart_service: CartService = Depends(get_cart_service),
):
    """Create a Mollie payment session."""
    # Get cart
    cart = await cart_service.get_cart(checkout_request.cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Build webhook URL from request origin
    base_url = str(request.base_url).rstrip("/")
    webhook_url = f"{base_url}/api/webhooks/mollie"

    # Create Mollie payment
    result = await mollie_service.create_payment(
        cart=cart,
        success_url=checkout_request.success_url,
        cancel_url=checkout_request.cancel_url,
        webhook_url=webhook_url,
    )

    return CheckoutResponse(
        checkout_url=result["url"],
        session_id=result["payment_id"],
    )
