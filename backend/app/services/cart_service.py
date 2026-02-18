"""Cart service for managing shopping carts."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate, CartResponse, CartItemResponse


class CartService:
    """Service for cart operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_cart(self) -> CartResponse:
        """Create a new shopping cart."""
        cart = Cart()
        self.db.add(cart)
        await self.db.commit()
        # Re-fetch with items loaded to avoid lazy loading issues
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == cart.id)
            .options(selectinload(Cart.items))
        )
        cart = result.scalar_one()
        return self._cart_to_response(cart)

    async def get_cart(self, cart_id: UUID) -> CartResponse | None:
        """Get cart by ID."""
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items))
        )
        cart = result.scalar_one_or_none()
        if not cart:
            return None
        return self._cart_to_response(cart)

    async def add_item(
        self,
        cart_id: UUID,
        item: CartItemCreate,
    ) -> CartResponse | None:
        """Add item to cart."""
        result = await self.db.execute(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.items))
        )
        cart = result.scalar_one_or_none()
        if not cart:
            return None

        # Check if item already exists (same product + variant)
        for existing in cart.items:
            if (
                existing.product_slug == item.product_slug
                and existing.variant == item.variant
            ):
                existing.quantity += item.quantity
                await self.db.commit()
                return await self.get_cart(cart_id)

        # Add new item
        cart_item = CartItem(
            cart_id=cart_id,
            product_slug=item.product_slug,
            product_name=item.product_name,
            variant=item.variant,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        self.db.add(cart_item)
        await self.db.commit()
        return await self.get_cart(cart_id)

    async def update_item(
        self,
        cart_id: UUID,
        item_id: UUID,
        quantity: int,
    ) -> CartResponse | None:
        """Update cart item quantity."""
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        if quantity <= 0:
            await self.db.delete(item)
        else:
            item.quantity = quantity

        await self.db.commit()
        return await self.get_cart(cart_id)

    async def remove_item(
        self,
        cart_id: UUID,
        item_id: UUID,
    ) -> CartResponse | None:
        """Remove item from cart."""
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        await self.db.delete(item)
        await self.db.commit()
        return await self.get_cart(cart_id)

    def _cart_to_response(self, cart: Cart) -> CartResponse:
        """Convert Cart model to response schema."""
        items = [
            CartItemResponse(
                id=item.id,
                product_slug=item.product_slug,
                product_name=item.product_name,
                variant=item.variant,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                subtotal=float(item.unit_price) * item.quantity,
            )
            for item in cart.items
        ]

        return CartResponse(
            id=cart.id,
            items=items,
            item_count=sum(item.quantity for item in items),
            subtotal=sum(item.subtotal for item in items),
            created_at=cart.created_at,
            expires_at=cart.expires_at,
        )
