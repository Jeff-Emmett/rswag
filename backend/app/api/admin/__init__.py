"""Admin API routes."""

from fastapi import APIRouter

from app.api.admin import auth, orders, analytics, products

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["admin-auth"])
router.include_router(orders.router, prefix="/orders", tags=["admin-orders"])
router.include_router(analytics.router, prefix="/analytics", tags=["admin-analytics"])
router.include_router(products.router, prefix="/products", tags=["admin-products"])
