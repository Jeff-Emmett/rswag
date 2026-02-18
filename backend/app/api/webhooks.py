"""Webhook endpoints for Mollie and POD providers."""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.mollie_service import MollieService
from app.services.order_service import OrderService

router = APIRouter()


def get_mollie_service() -> MollieService:
    return MollieService()


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


@router.post("/mollie")
async def mollie_webhook(
    request: Request,
    mollie_service: MollieService = Depends(get_mollie_service),
    order_service: OrderService = Depends(get_order_service),
):
    """Handle Mollie webhook events.

    Mollie sends a POST with form data containing just the payment ID.
    We then fetch the full payment details from Mollie's API to verify status.
    """
    form = await request.form()
    payment_id = form.get("id")

    if not payment_id:
        raise HTTPException(status_code=400, detail="Missing payment id")

    # Fetch payment from Mollie API (this IS the verification — no signature needed)
    payment = await mollie_service.get_payment(payment_id)

    status = payment.get("status")
    if status == "paid":
        await order_service.handle_successful_payment(payment)
    elif status in ("failed", "canceled", "expired"):
        # Log but no action needed
        print(f"Mollie payment {payment_id} status: {status}")

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
