"""Printful Print-on-Demand API client (v2).

Handles catalog lookup, mockup generation, and order submission.
API v2 docs: https://developers.printful.com/docs/v2-beta/
Rate limit: 120 req/60s (leaky bucket), lower for mockups.
"""

import asyncio
import logging
import time

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BASE_URL = "https://api.printful.com/v2"

# In-memory cache for catalog variants: {product_id: {"variants": [...], "ts": float}}
_variant_cache: dict[int, dict] = {}
_VARIANT_CACHE_TTL = 86400  # 24 hours


class PrintfulClient:
    """Client for the Printful v2 API."""

    def __init__(self):
        self.api_token = settings.printful_api_token
        self.sandbox = settings.pod_sandbox_mode
        self.enabled = bool(self.api_token)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    # ── Catalog ──

    async def get_catalog_variants(self, product_id: int) -> list[dict]:
        """Get variants for a catalog product (cached 24h).

        Each variant has: id (int), size (str), color (str), color_code (str).
        """
        cached = _variant_cache.get(product_id)
        if cached and (time.time() - cached["ts"]) < _VARIANT_CACHE_TTL:
            return cached["variants"]

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{BASE_URL}/catalog-products/{product_id}/catalog-variants",
                headers=self._headers,
            )
            resp.raise_for_status()
            variants = resp.json().get("data", [])

        _variant_cache[product_id] = {"variants": variants, "ts": time.time()}
        return variants

    async def resolve_variant_id(
        self,
        product_id: int,
        size: str,
        color: str = "Black",
    ) -> int | None:
        """Resolve (product_id, size, color) → Printful catalog_variant_id.

        Our metadata uses SKU "71" + variants ["S","M","L",...].
        Printful orders require numeric catalog_variant_id.
        """
        variants = await self.get_catalog_variants(product_id)

        # Try exact match on size + color
        for v in variants:
            if (
                v.get("size", "").upper() == size.upper()
                and color.lower() in v.get("color", "").lower()
            ):
                return v.get("id")

        # Fallback: match size only
        for v in variants:
            if v.get("size", "").upper() == size.upper():
                return v.get("id")

        return None

    # ── Mockup Generation ──

    async def create_mockup_task(
        self,
        product_id: int,
        variant_ids: list[int],
        image_url: str,
        placement: str = "front_large",
    ) -> str:
        """Start async mockup generation task.

        Returns task_id to poll with get_mockup_task().
        """
        payload = {
            "product_id": product_id,
            "variant_ids": variant_ids,
            "format": "png",
            "placements": [
                {
                    "placement": placement,
                    "image_url": image_url,
                }
            ],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BASE_URL}/mockup-tasks",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            task_id = data.get("task_key") or data.get("id") or data.get("task_id")
            logger.info(f"Printful mockup task created: {task_id}")
            return str(task_id)

    async def get_mockup_task(self, task_id: str) -> dict:
        """Poll mockup task status.

        Returns dict with "status" (pending/completed/failed) and
        "mockups" list when completed.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{BASE_URL}/mockup-tasks",
                headers=self._headers,
                params={"task_key": task_id},
            )
            resp.raise_for_status()
            return resp.json().get("data", {})

    async def generate_mockup_and_wait(
        self,
        product_id: int,
        variant_ids: list[int],
        image_url: str,
        placement: str = "front_large",
        max_polls: int = 20,
        poll_interval: float = 3.0,
    ) -> list[dict] | None:
        """Create mockup task and poll until complete.

        Returns list of mockup dicts with "mockup_url" fields,
        or None on failure/timeout.
        """
        task_id = await self.create_mockup_task(
            product_id, variant_ids, image_url, placement
        )

        for _ in range(max_polls):
            await asyncio.sleep(poll_interval)
            result = await self.get_mockup_task(task_id)
            status = result.get("status", "")

            if status == "completed":
                return (
                    result.get("mockups", [])
                    or result.get("catalog_variant_mockups", [])
                )
            elif status == "failed":
                reasons = result.get("failure_reasons", [])
                logger.error(f"Mockup task {task_id} failed: {reasons}")
                return None

        logger.warning(f"Mockup task {task_id} timed out after {max_polls} polls")
        return None

    # ── Orders ──

    async def create_order(
        self,
        items: list[dict],
        recipient: dict,
    ) -> dict:
        """Create a fulfillment order.

        Args:
            items: List of dicts with:
                - catalog_variant_id (int)
                - quantity (int)
                - image_url (str) — public URL to design
                - placement (str, default "front_large")
            recipient: dict with name, address1, city, state_code,
                       country_code, zip, email (optional)
        """
        if not self.enabled:
            raise ValueError("Printful API token not configured")

        order_items = []
        for item in items:
            order_items.append({
                "source": "catalog",
                "catalog_variant_id": item["catalog_variant_id"],
                "quantity": item.get("quantity", 1),
                "placements": [
                    {
                        "placement": item.get("placement", "front_large"),
                        "technique": "dtg",
                        "layers": [
                            {
                                "type": "file",
                                "url": item["image_url"],
                            }
                        ],
                    }
                ],
            })

        payload = {
            "recipient": recipient,
            "items": order_items,
        }

        # Sandbox mode: create as draft (not sent to production)
        if self.sandbox:
            payload["draft"] = True

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BASE_URL}/orders",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json().get("data", {})
            logger.info(f"Printful order created: {result.get('id')}")
            return result

    async def get_order(self, order_id: str) -> dict:
        """Get order details by Printful order ID."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{BASE_URL}/orders/{order_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json().get("data", {})
