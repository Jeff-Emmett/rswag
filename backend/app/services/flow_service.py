"""Flow service client for TBFF revenue routing.

After a swag sale, the margin (sale price minus POD fulfillment cost)
gets deposited into a TBFF funnel via the flow-service. The flow-service
manages threshold-based distribution, and when the funnel overflows its
MAX threshold, excess funds route to the bonding curve.

Revenue split flow:
  Mollie payment → calculate margin → deposit to flow-service funnel
                                         ↓
                                    TBFF thresholds
                                    ↓ overflow
                                bonding curve ($MYCO)
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FlowService:
    """Client for the payment-infra flow-service."""

    def __init__(self):
        self.base_url = settings.flow_service_url.rstrip("/")
        self.flow_id = settings.flow_id
        self.funnel_id = settings.flow_funnel_id
        self.enabled = bool(self.base_url and self.flow_id and self.funnel_id)

    async def deposit_revenue(
        self,
        amount: float,
        currency: str = "USD",
        order_id: str | None = None,
        description: str | None = None,
    ) -> dict | None:
        """Deposit revenue margin into the TBFF funnel.

        Args:
            amount: Fiat amount to deposit (post-split margin)
            currency: Currency code (default USD)
            order_id: rSwag order ID for traceability
            description: Human-readable note
        """
        if not self.enabled:
            logger.info("Flow service not configured, skipping revenue deposit")
            return None

        if amount <= 0:
            return None

        payload = {
            "funnelId": self.funnel_id,
            "amount": round(amount, 2),
            "currency": currency,
            "source": "rswag",
            "metadata": {},
        }
        if order_id:
            payload["metadata"]["order_id"] = order_id
        if description:
            payload["metadata"]["description"] = description

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/flows/{self.flow_id}/deposit",
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()
                logger.info(
                    f"Revenue deposited to flow: ${amount:.2f} {currency} "
                    f"(order={order_id})"
                )
                return result
        except httpx.HTTPError as e:
            logger.error(f"Failed to deposit revenue to flow service: {e}")
            return None

    async def get_flow_stats(self) -> dict | None:
        """Get current flow stats (balance, thresholds, etc.)."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/flows/{self.flow_id}",
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get flow stats: {e}")
            return None
