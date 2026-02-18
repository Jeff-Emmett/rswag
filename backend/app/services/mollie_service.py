"""Mollie payment service."""

from mollie.api.client import Client

from app.config import get_settings
from app.schemas.cart import CartResponse

settings = get_settings()


class MollieService:
    """Service for Mollie payment operations."""

    def __init__(self):
        self.client = Client()
        if settings.mollie_api_key:
            self.client.set_api_key(settings.mollie_api_key)

    async def create_payment(
        self,
        cart: CartResponse,
        success_url: str,
        cancel_url: str,
        webhook_url: str,
    ) -> dict:
        """Create a Mollie payment.

        Mollie uses a redirect flow: create payment → redirect to hosted page →
        webhook callback on completion → redirect to success URL.
        """
        # Build description from cart items
        item_names = [item.product_name for item in cart.items]
        description = f"rSwag order: {', '.join(item_names[:3])}"
        if len(item_names) > 3:
            description += f" (+{len(item_names) - 3} more)"

        # Calculate total from cart
        total = sum(item.unit_price * item.quantity for item in cart.items)

        payment = self.client.payments.create({
            "amount": {
                "currency": "USD",
                "value": f"{total:.2f}",
            },
            "description": description,
            "redirectUrl": f"{success_url}?payment_id={{paymentId}}",
            "cancelUrl": cancel_url,
            "webhookUrl": webhook_url,
            "metadata": {
                "cart_id": str(cart.id),
            },
        })

        return {
            "url": payment["_links"]["checkout"]["href"],
            "payment_id": payment["id"],
        }

    async def get_payment(self, payment_id: str) -> dict:
        """Get Mollie payment details."""
        payment = self.client.payments.get(payment_id)
        return payment

    async def create_refund(
        self,
        payment_id: str,
        amount: float | None = None,
        currency: str = "USD",
    ) -> dict:
        """Create a refund for a Mollie payment."""
        payment = self.client.payments.get(payment_id)
        refund_data = {}
        if amount is not None:
            refund_data["amount"] = {
                "currency": currency,
                "value": f"{amount:.2f}",
            }
        refund = self.client.payment_refunds.with_parent_id(payment_id).create(refund_data)
        return refund
