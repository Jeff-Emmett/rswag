"""Admin analytics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import get_current_admin

router = APIRouter()


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/sales")
async def get_sales_analytics(
    days: int = Query(default=30, le=365),
    service: AnalyticsService = Depends(get_analytics_service),
    _admin=Depends(get_current_admin),
):
    """Get sales analytics (admin only)."""
    start_date = datetime.utcnow() - timedelta(days=days)
    return await service.get_sales_summary(start_date)


@router.get("/products")
async def get_product_analytics(
    days: int = Query(default=30, le=365),
    limit: int = Query(default=10, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
    _admin=Depends(get_current_admin),
):
    """Get product performance analytics (admin only)."""
    start_date = datetime.utcnow() - timedelta(days=days)
    return await service.get_product_performance(start_date, limit)
