"""
Paystack integration — card / international payments.

Flow:
  1. POST /api/payments/initiate  (method=card)
     → backend calls Paystack /transaction/initialize
     → returns {authorization_url, access_code, reference}
  2. Frontend redirects to authorization_url  OR  uses Paystack inline JS with access_code
  3. Paystack redirects to callback_url after payment
  4. POST /api/payments/{payment_id}/verify  → polls Paystack and syncs DB status
  5. Webhook (optional): POST /api/payments/webhook/paystack
     → verified via HMAC-SHA512 using the secret key — no separate webhook secret needed

Docs: https://paystack.com/docs/payments/accept-payments
"""

import hashlib
import hmac

import httpx

from app.config import settings

_BASE = "https://api.paystack.co"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }


def initialize_transaction(
    *,
    amount_ugx: int,
    email: str,
    reference: str,
    booking_id: str,
    callback_url: str,
) -> dict:
    """
    Initialize a Paystack transaction.
    Returns Paystack response with data.authorization_url, data.access_code, data.reference.
    Amount is in UGX (whole shillings — UGX has no subdivision).
    """
    payload = {
        "email": email,
        "amount": amount_ugx,
        "currency": "UGX",
        "reference": reference,
        "callback_url": callback_url,
        "metadata": {"booking_id": booking_id},
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{_BASE}/transaction/initialize", headers=_headers(), json=payload
        )
        resp.raise_for_status()
        return resp.json()


def verify_transaction(reference: str) -> dict:
    """Verify a transaction by its reference. Returns the raw Paystack API response."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{_BASE}/transaction/verify/{reference}", headers=_headers())
        resp.raise_for_status()
        return resp.json()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Paystack signs webhooks with HMAC-SHA512 using your secret key.
    No separate webhook secret is needed.
    """
    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
