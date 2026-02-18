"""Webhook endpoints for Stripe and POD providers."""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.services.stripe_service import StripeService
from app.services.order_service import OrderService

router = APIRouter()
settings = get_settings()


def get_stripe_service() -> StripeService:
    return StripeService()


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service),
    order_service: OrderService = Depends(get_order_service),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        event = stripe_service.verify_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await order_service.handle_successful_payment(session)

    elif event["type"] == "payment_intent.payment_failed":
        # Log failure, maybe send notification
        pass

    return {"status": "ok"}


@router.post("/prodigi")
async def prodigi_webhook(
    request: Request,
    order_service: OrderService = Depends(get_order_service),
):
    """Handle Prodigi webhook events."""
    payload = await request.json()

    event_type = payload.get("event")
    order_data = payload.get("order", {})

    if event_type in ["order.shipped", "order.complete"]:
        await order_service.update_pod_status(
            pod_provider="prodigi",
            pod_order_id=order_data.get("id"),
            status=event_type.replace("order.", ""),
            tracking_number=order_data.get("shipments", [{}])[0].get("trackingNumber"),
            tracking_url=order_data.get("shipments", [{}])[0].get("trackingUrl"),
        )

    return {"status": "ok"}


@router.post("/printful")
async def printful_webhook(
    request: Request,
    order_service: OrderService = Depends(get_order_service),
):
    """Handle Printful webhook events."""
    payload = await request.json()

    event_type = payload.get("type")
    order_data = payload.get("data", {}).get("order", {})

    if event_type in ["package_shipped", "order_fulfilled"]:
        shipment = payload.get("data", {}).get("shipment", {})
        await order_service.update_pod_status(
            pod_provider="printful",
            pod_order_id=str(order_data.get("id")),
            status="shipped" if event_type == "package_shipped" else "fulfilled",
            tracking_number=shipment.get("tracking_number"),
            tracking_url=shipment.get("tracking_url"),
        )

    return {"status": "ok"}
