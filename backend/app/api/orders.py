"""Orders API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import OrderResponse
from app.services.order_service import OrderService

router = APIRouter()


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    email: str = Query(..., description="Email used for the order"),
    service: OrderService = Depends(get_order_service),
):
    """Get order by ID (requires email verification)."""
    order = await service.get_order_by_id_and_email(order_id, email)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: UUID,
    email: str = Query(..., description="Email used for the order"),
    service: OrderService = Depends(get_order_service),
):
    """Get tracking information for an order."""
    order = await service.get_order_by_id_and_email(order_id, email)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tracking = []
    for item in order.items:
        if item.pod_tracking_number:
            tracking.append({
                "product": item.product_name,
                "tracking_number": item.pod_tracking_number,
                "tracking_url": item.pod_tracking_url,
                "status": item.pod_status,
            })

    return {"order_id": order_id, "tracking": tracking}
