"""Order management service."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.order import Order, OrderItem, OrderStatus
from app.models.customer import Customer
from app.models.cart import Cart
from app.schemas.order import OrderResponse, OrderItemResponse
from app.services.flow_service import FlowService
from app.pod.printful_client import PrintfulClient
from app.pod.prodigi_client import ProdigiClient
from app.services.design_service import DesignService

logger = logging.getLogger(__name__)
settings = get_settings()


class OrderService:
    """Service for order operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order_by_id(self, order_id: UUID) -> OrderResponse | None:
        """Get order by ID."""
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        return self._order_to_response(order)

    async def get_order_by_id_and_email(
        self,
        order_id: UUID,
        email: str,
    ) -> OrderResponse | None:
        """Get order by ID with email verification."""
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id, Order.shipping_email == email)
            .options(selectinload(Order.items))
        )
        order = result.scalar_one_or_none()
        if not order:
            return None
        return self._order_to_response(order)

    async def list_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OrderResponse]:
        """List orders with optional status filter."""
        query = select(Order).options(selectinload(Order.items))
        if status:
            query = query.where(Order.status == status.value)
        query = query.order_by(Order.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        orders = result.scalars().all()
        return [self._order_to_response(o) for o in orders]

    async def update_status(
        self,
        order_id: UUID,
        status: OrderStatus,
    ) -> OrderResponse | None:
        """Update order status."""
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        order = result.scalar_one_or_none()
        if not order:
            return None

        order.status = status.value
        if status == OrderStatus.SHIPPED:
            order.shipped_at = datetime.utcnow()
        elif status == OrderStatus.DELIVERED:
            order.delivered_at = datetime.utcnow()

        await self.db.commit()
        return self._order_to_response(order)

    async def handle_successful_payment(self, payment: dict):
        """Handle successful Mollie payment.

        Called by the Mollie webhook when payment status is 'paid'.
        Mollie payment object contains metadata with cart_id.
        """
        cart_id = payment.get("metadata", {}).get("cart_id")
        if not cart_id:
            return

        # Get cart
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == UUID(cart_id))
            .options(selectinload(Cart.items))
        )
        cart = result.scalar_one_or_none()
        if not cart or not cart.items:
            return

        # Extract amount from Mollie payment
        amount = payment.get("amount", {})
        total = float(amount.get("value", "0"))
        currency = amount.get("currency", "USD")

        # Create order
        order = Order(
            payment_provider="mollie",
            payment_id=payment.get("id"),
            payment_method=payment.get("method"),
            status=OrderStatus.PAID.value,
            shipping_email=payment.get("metadata", {}).get("email", ""),
            subtotal=total,
            total=total,
            currency=currency,
            paid_at=datetime.utcnow(),
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_slug=cart_item.product_slug,
                product_name=cart_item.product_name,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                unit_price=float(cart_item.unit_price),
                pod_status="pending",
            )
            self.db.add(order_item)

        await self.db.commit()

        # Route revenue margin to TBFF flow → bonding curve
        await self._deposit_revenue_to_flow(order)

        # Submit to POD providers
        await self._submit_to_pod(order)

        # TODO: Send confirmation email

    async def update_pod_status(
        self,
        pod_provider: str,
        pod_order_id: str,
        status: str,
        tracking_number: str | None = None,
        tracking_url: str | None = None,
    ):
        """Update POD status for order items."""
        await self.db.execute(
            update(OrderItem)
            .where(
                OrderItem.pod_provider == pod_provider,
                OrderItem.pod_order_id == pod_order_id,
            )
            .values(
                pod_status=status,
                pod_tracking_number=tracking_number,
                pod_tracking_url=tracking_url,
            )
        )
        await self.db.commit()

    async def _submit_to_pod(self, order: Order):
        """Route order items to the correct POD provider for fulfillment.

        Reads each item's design metadata to determine provider (printful/prodigi),
        groups items, and submits separate orders per provider.
        """
        if not order.shipping_address_line1:
            logger.info(f"Order {order.id} has no shipping address, skipping POD")
            return

        design_service = DesignService()
        printful_items = []
        prodigi_items = []

        for item in order.items:
            image_url = f"https://fungiswag.jeffemmett.com/api/designs/{item.product_slug}/image"

            design = await design_service.get_design(item.product_slug)
            provider = "prodigi"  # default
            product_sku = item.variant or item.product_slug

            if design and design.products:
                product_config = design.products[0]
                provider = product_config.provider
                product_sku = product_config.sku

            if provider == "printful":
                # Extract size from variant string (e.g. "71-M" → "M", or just "M")
                size = item.variant or "M"
                if "-" in size:
                    size = size.split("-", 1)[1]

                printful_items.append({
                    "order_item": item,
                    "product_id": int(product_sku),
                    "size": size,
                    "quantity": item.quantity,
                    "image_url": image_url,
                })
            else:
                prodigi_items.append({
                    "order_item": item,
                    "sku": item.variant or item.product_slug,
                    "quantity": item.quantity,
                    "image_url": image_url,
                })

        if printful_items:
            await self._submit_to_printful(order, printful_items)
        if prodigi_items:
            await self._submit_to_prodigi(order, prodigi_items)

    async def _submit_to_printful(self, order: Order, items: list[dict]):
        """Submit items to Printful for fulfillment."""
        printful = PrintfulClient()
        if not printful.enabled:
            logger.info("Printful not configured, skipping")
            return

        order_items = []
        for item_data in items:
            variant_id = await printful.resolve_variant_id(
                product_id=item_data["product_id"],
                size=item_data["size"],
            )
            if not variant_id:
                logger.error(
                    f"Could not resolve Printful variant for product "
                    f"{item_data['product_id']} size {item_data['size']}"
                )
                continue

            order_items.append({
                "catalog_variant_id": variant_id,
                "quantity": item_data["quantity"],
                "image_url": item_data["image_url"],
                "placement": "front_large",
            })

        if not order_items:
            return

        recipient = {
            "name": order.shipping_name or "",
            "address1": order.shipping_address_line1 or "",
            "address2": order.shipping_address_line2 or "",
            "city": order.shipping_city or "",
            "state_code": order.shipping_state or "",
            "country_code": order.shipping_country or "",
            "zip": order.shipping_postal_code or "",
            "email": order.shipping_email or "",
        }

        try:
            result = await printful.create_order(
                items=order_items,
                recipient=recipient,
            )
            pod_order_id = str(result.get("id", ""))

            for item_data in items:
                item_data["order_item"].pod_provider = "printful"
                item_data["order_item"].pod_order_id = pod_order_id
                item_data["order_item"].pod_status = "submitted"

            order.status = OrderStatus.PROCESSING.value
            await self.db.commit()
            logger.info(f"Submitted order {order.id} to Printful: {pod_order_id}")

        except Exception as e:
            logger.error(f"Failed to submit order {order.id} to Printful: {e}")

    async def _submit_to_prodigi(self, order: Order, items: list[dict]):
        """Submit items to Prodigi for fulfillment."""
        prodigi = ProdigiClient()
        if not prodigi.enabled:
            logger.info("Prodigi not configured, skipping")
            return

        prodigi_items = []
        for item_data in items:
            prodigi_items.append({
                "sku": item_data["sku"],
                "copies": item_data["quantity"],
                "sizing": "fillPrintArea",
                "assets": [{"printArea": "default", "url": item_data["image_url"]}],
            })

        recipient = {
            "name": order.shipping_name or "",
            "email": order.shipping_email or "",
            "address": {
                "line1": order.shipping_address_line1 or "",
                "line2": order.shipping_address_line2 or "",
                "townOrCity": order.shipping_city or "",
                "stateOrCounty": order.shipping_state or "",
                "postalOrZipCode": order.shipping_postal_code or "",
                "countryCode": order.shipping_country or "",
            },
        }

        try:
            result = await prodigi.create_order(
                items=prodigi_items,
                recipient=recipient,
                metadata={"rswag_order_id": str(order.id)},
            )
            pod_order_id = result.get("id")

            for item_data in items:
                item_data["order_item"].pod_provider = "prodigi"
                item_data["order_item"].pod_order_id = pod_order_id
                item_data["order_item"].pod_status = "submitted"

            order.status = OrderStatus.PROCESSING.value
            await self.db.commit()
            logger.info(f"Submitted order {order.id} to Prodigi: {pod_order_id}")

        except Exception as e:
            logger.error(f"Failed to submit order {order.id} to Prodigi: {e}")

    async def _deposit_revenue_to_flow(self, order: Order):
        """Calculate margin and deposit to TBFF flow for bonding curve funding.

        Revenue split:
          total sale - POD cost estimate = margin
          margin × flow_revenue_split = amount deposited to flow
          flow → Transak on-ramp → USDC → bonding curve → $MYCO
        """
        split = settings.flow_revenue_split
        if split <= 0:
            return

        total = float(order.total) if order.total else 0
        if total <= 0:
            return

        # Revenue split: configurable fraction of total goes to flow
        # (POD costs + operational expenses kept as fiat remainder)
        flow_amount = round(total * split, 2)

        flow_service = FlowService()
        await flow_service.deposit_revenue(
            amount=flow_amount,
            currency=order.currency or "USD",
            order_id=str(order.id),
            description=f"rSwag sale revenue split ({split:.0%} of ${total:.2f})",
        )

    async def _get_or_create_customer(self, email: str) -> Customer | None:
        """Get or create customer by email."""
        if not email:
            return None

        result = await self.db.execute(
            select(Customer).where(Customer.email == email)
        )
        customer = result.scalar_one_or_none()
        if customer:
            return customer

        customer = Customer(email=email)
        self.db.add(customer)
        await self.db.flush()
        return customer

    def _order_to_response(self, order: Order) -> OrderResponse:
        """Convert Order model to response schema."""
        items = [
            OrderItemResponse(
                id=item.id,
                product_slug=item.product_slug,
                product_name=item.product_name,
                variant=item.variant,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                pod_provider=item.pod_provider,
                pod_status=item.pod_status,
                pod_tracking_number=item.pod_tracking_number,
                pod_tracking_url=item.pod_tracking_url,
            )
            for item in order.items
        ]

        return OrderResponse(
            id=order.id,
            status=order.status,
            shipping_name=order.shipping_name,
            shipping_email=order.shipping_email,
            shipping_city=order.shipping_city,
            shipping_country=order.shipping_country,
            subtotal=float(order.subtotal) if order.subtotal else None,
            shipping_cost=float(order.shipping_cost) if order.shipping_cost else None,
            tax=float(order.tax) if order.tax else None,
            total=float(order.total) if order.total else None,
            currency=order.currency,
            items=items,
            created_at=order.created_at,
            paid_at=order.paid_at,
            shipped_at=order.shipped_at,
        )
