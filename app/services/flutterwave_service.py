"""
Flutterwave integration — MTN Uganda Mobile Money & Airtel Money.

Supported networks:
  - MTN_UGANDA  (network code used in FLW API)
  - AIRTEL_UGANDA

Flow (direct charge):
  1. POST /api/payments/initiate  (method=mobile_money, channel=MTN_UGANDA|AIRTEL_UGANDA)
     → FLW initiates a push USSD prompt to the customer's phone
     → returns {flw_ref, payment_id, status="pending"}
  2. Customer approves on their phone (USSD PIN)
  3. FLW calls POST /api/payments/webhook  → updates Payment row to "completed"
     OR call POST /api/payments/{payment_id}/verify to poll status manually (no webhook secret needed)

Docs: https://developer.flutterwave.com/reference/mobile-money
"""

from typing import Literal

import httpx

from app.config import settings

MOBILE_NETWORKS = Literal["MTN_UGANDA", "AIRTEL_UGANDA"]

_HEADERS = {
    "Authorization": f"Bearer {settings.flutterwave_secret_key}",
    "Content-Type": "application/json",
}


def charge_mobile_money(
    *,
    tx_ref: str,
    amount_ugx: int,
    phone_number: str,
    network: MOBILE_NETWORKS,
    customer_email: str,
    customer_name: str,
    booking_id: str,
) -> dict:
    """
    Initiate a mobile money charge. Returns the raw FLW API response dict.
    On success the response contains status="success" and data.status="pending".
    The customer receives a USSD push prompt to approve on their phone.
    """
    payload = {
        "tx_ref": tx_ref,
        "amount": str(amount_ugx),
        "currency": "UGX",
        "network": network,
        "email": customer_email,
        "phone_number": phone_number,
        "fullname": customer_name,
        "meta": {"booking_id": booking_id},
        "redirect_url": settings.payment_redirect_url,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{settings.flutterwave_base_url}/charges?type=mobile_money_uganda",
            headers=_HEADERS,
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


def verify_transaction(tx_ref: str) -> dict:
    """Verify a transaction by our tx_ref. Returns the raw API response."""
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{settings.flutterwave_base_url}/transactions/verify_by_reference",
            headers=_HEADERS,
            params={"tx_ref": tx_ref},
        )
        resp.raise_for_status()
        return resp.json()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Flutterwave webhook signature using the secret key."""
    import hashlib
    import hmac

    expected = hmac.new(
        settings.flutterwave_secret_key.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
