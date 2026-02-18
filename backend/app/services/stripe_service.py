"""Stripe payment service."""

import stripe

from app.config import get_settings
from app.schemas.cart import CartResponse

settings = get_settings()

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for Stripe operations."""

    async def create_checkout_session(
        self,
        cart: CartResponse,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        """Create a Stripe checkout session."""
        line_items = []
        for item in cart.items:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.product_name,
                        "description": f"Variant: {item.variant}" if item.variant else None,
                    },
                    "unit_amount": int(item.unit_price * 100),  # Convert to cents
                },
                "quantity": item.quantity,
            })

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            shipping_address_collection={
                "allowed_countries": [
                    "US", "CA", "GB", "AU", "DE", "FR", "NL", "BE", "AT", "CH",
                    "ES", "IT", "PT", "IE", "DK", "SE", "NO", "FI", "PL", "CZ",
                ],
            },
            metadata={
                "cart_id": str(cart.id),
            },
        )

        return {
            "url": session.url,
            "session_id": session.id,
        }

    def verify_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Verify and parse Stripe webhook."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret,
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {e}")
        except Exception as e:
            raise ValueError(f"Webhook error: {e}")

    async def get_session(self, session_id: str) -> dict:
        """Get Stripe checkout session details."""
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["line_items", "customer"],
        )
        return session

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: int | None = None,
    ) -> dict:
        """Create a refund for a payment."""
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=amount,  # None = full refund
        )
        return refund
