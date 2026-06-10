"""
Stripe integration — card / international payments.

Flow:
  1. POST /api/payments/initiate  (method=card)  → returns {client_secret, payment_id}
  2. Frontend uses Stripe.js to confirm the PaymentIntent
  3. Stripe calls POST /api/payments/webhook  → updates Payment row to "completed"
"""

from datetime import datetime, timezone

import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key


def create_payment_intent(
    amount_usd_cents: int, booking_id: str, customer_email: str
) -> dict:
    """Create a Stripe PaymentIntent and return {payment_intent_id, client_secret}."""
    intent = stripe.PaymentIntent.create(
        amount=amount_usd_cents,
        currency=settings.stripe_currency,
        payment_method_types=["card"],
        metadata={"booking_id": booking_id, "customer_email": customer_email},
    )
    return {"payment_intent_id": intent.id, "client_secret": intent.client_secret}


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and parse a Stripe webhook payload. Raises stripe.error.SignatureVerificationError on failure."""
    return stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )


def get_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
    return stripe.PaymentIntent.retrieve(payment_intent_id)


def refund_payment_intent(
    payment_intent_id: str, amount_cents: int | None = None
) -> stripe.Refund:
    """Full refund if amount_cents is None, partial otherwise."""
    kwargs: dict = {"payment_intent": payment_intent_id}
    if amount_cents is not None:
        kwargs["amount"] = amount_cents
    return stripe.Refund.create(**kwargs)
