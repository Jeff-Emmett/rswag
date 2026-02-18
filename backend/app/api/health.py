"""Health check endpoint."""

from fastapi import APIRouter

from app.config import get_settings
from app.services.flow_service import FlowService

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    flow_service = FlowService()
    return {
        "status": "healthy",
        "payment_provider": "mollie",
        "flow_enabled": flow_service.enabled,
        "flow_revenue_split": settings.flow_revenue_split if flow_service.enabled else None,
    }
