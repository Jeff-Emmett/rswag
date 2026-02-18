"""Prodigi Print-on-Demand API client (v4).

Handles order submission, product specs, and quotes.
Sandbox: https://api.sandbox.prodigi.com/v4.0/
Production: https://api.prodigi.com/v4.0/
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SANDBOX_URL = "https://api.sandbox.prodigi.com/v4.0"
PRODUCTION_URL = "https://api.prodigi.com/v4.0"


class ProdigiClient:
    """Client for the Prodigi v4 Print API."""

    def __init__(self):
        self.api_key = settings.prodigi_api_key
        self.base_url = SANDBOX_URL if settings.pod_sandbox_mode else PRODUCTION_URL
        self.enabled = bool(self.api_key)

    @property
    def _headers(self) -> dict:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_order(
        self,
        items: list[dict],
        recipient: dict,
        shipping_method: str = "Budget",
        metadata: dict | None = None,
    ) -> dict:
        """Create a Prodigi print order.

        Args:
            items: List of items, each with:
                - sku: Prodigi SKU (e.g., "GLOBAL-STI-KIS-4X4")
                - copies: Number of copies
                - sizing: "fillPrintArea" | "fitPrintArea" | "stretchToPrintArea"
                - assets: [{"printArea": "default", "url": "https://..."}]
            recipient: Shipping address with:
                - name: Recipient name
                - email: Email (optional)
                - address: {line1, line2, townOrCity, stateOrCounty, postalOrZipCode, countryCode}
            shipping_method: "Budget" | "Standard" | "Express"
            metadata: Optional key/value metadata
        """
        if not self.enabled:
            raise ValueError("Prodigi API key not configured")

        payload = {
            "shippingMethod": shipping_method,
            "recipient": recipient,
            "items": items,
        }
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/Orders",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"Prodigi order created: {result.get('id')}")
            return result

    async def get_order(self, order_id: str) -> dict:
        """Get order details by Prodigi order ID."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/Orders/{order_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_product(self, sku: str) -> dict:
        """Get product specifications (dimensions, print areas, etc.)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/products/{sku}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_quote(
        self,
        items: list[dict],
        shipping_method: str = "Budget",
        destination_country: str = "US",
    ) -> dict:
        """Get a pricing quote before ordering.

        Args:
            items: List with sku, copies, sizing, assets
            shipping_method: Shipping tier
            destination_country: 2-letter country code
        """
        payload = {
            "shippingMethod": shipping_method,
            "destinationCountryCode": destination_country,
            "items": [
                {"sku": item["sku"], "copies": item.get("copies", 1)}
                for item in items
            ],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/quotes",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
