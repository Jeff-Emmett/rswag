"""Order management service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.models.customer import Customer
from app.models.cart import Cart
from app.schemas.order import OrderResponse, OrderItemResponse


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

    async def handle_successful_payment(self, session: dict):
        """Handle successful Stripe payment."""
        cart_id = session.get("metadata", {}).get("cart_id")
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

        # Get or create customer
        email = session.get("customer_details", {}).get("email", "")
        customer = await self._get_or_create_customer(email)

        # Get shipping details
        shipping = session.get("shipping_details", {}) or {}
        address = shipping.get("address", {}) or {}

        # Create order
        order = Order(
            customer_id=customer.id if customer else None,
            stripe_session_id=session.get("id"),
            stripe_payment_intent_id=session.get("payment_intent"),
            status=OrderStatus.PAID.value,
            shipping_name=shipping.get("name"),
            shipping_email=email,
            shipping_address_line1=address.get("line1"),
            shipping_address_line2=address.get("line2"),
            shipping_city=address.get("city"),
            shipping_state=address.get("state"),
            shipping_postal_code=address.get("postal_code"),
            shipping_country=address.get("country"),
            subtotal=float(session.get("amount_subtotal", 0)) / 100,
            shipping_cost=float(session.get("shipping_cost", {}).get("amount_total", 0)) / 100,
            total=float(session.get("amount_total", 0)) / 100,
            currency=session.get("currency", "usd").upper(),
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

        # TODO: Submit to POD providers
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
