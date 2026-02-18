"""Admin order management endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import OrderResponse, OrderStatus
from app.services.order_service import OrderService
from app.services.auth_service import get_current_admin

router = APIRouter()


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(db)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    status: OrderStatus | None = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrderService = Depends(get_order_service),
    _admin=Depends(get_current_admin),
):
    """List all orders (admin only)."""
    orders = await service.list_orders(status=status, limit=limit, offset=offset)
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    service: OrderService = Depends(get_order_service),
    _admin=Depends(get_current_admin),
):
    """Get order details (admin only)."""
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status: OrderStatus,
    service: OrderService = Depends(get_order_service),
    _admin=Depends(get_current_admin),
):
    """Update order status (admin only)."""
    order = await service.update_status(order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"status": "updated", "order_id": order_id, "new_status": status}
