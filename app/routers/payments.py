"""
Payment router — Paystack (card/international) + Flutterwave (MTN/Airtel Uganda MoMo).

Endpoints:
  POST /api/payments/initiate              — create payment record, return gateway data
  POST /api/payments/{payment_id}/verify   — manually verify & sync status (no webhook needed, good for testing)
  POST /api/payments/webhook/paystack      — Paystack webhook (HMAC-SHA512 with secret key, no JWT)
  POST /api/payments/webhook/flutterwave   — Flutterwave webhook (signature-verified, no JWT)
  GET  /api/payments/{booking_id}/status   — poll payment status
  GET  /api/payments/callback              — redirect after hosted checkout
"""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_current_user, DbSession
from app.models.booking import Booking
from app.models.commission import Commission
from app.models.payment import Payment, Payout
from app.models.vehicle import Vehicle
from app.services import paystack_service, flutterwave_service

router = APIRouter(prefix="/payments", tags=["payments"])


# ── Stripe public config (no auth required) ────────────────────────────────────

@router.get("/stripe-config")
def stripe_config():
    return {"publishable_key": settings.stripe_publishable_key}


# ── Schemas ────────────────────────────────────────────────────────────────────

class PaymentInitiateRequest(BaseModel):
    booking_id: str
    method: Literal["card", "mobile_money"]
    # Required for mobile_money
    phone_number: Optional[str] = None
    network: Optional[Literal["MTN_UGANDA", "AIRTEL_UGANDA"]] = None


class PaymentInitiateResponse(BaseModel):
    payment_id: str
    method: str
    status: str
    # Paystack
    authorization_url: Optional[str] = None
    access_code: Optional[str] = None
    reference: Optional[str] = None
    public_key: Optional[str] = None
    # Flutterwave
    flw_ref: Optional[str] = None
    message: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_booking_or_404(db: Session, booking_id: str, user_id: str) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != user_id:
        raise HTTPException(status_code=403, detail="Not your booking")
    if booking.status not in ("pending", "pending_payment", "confirmed"):
        raise HTTPException(status_code=400, detail=f"Booking status '{booking.status}' cannot be paid")
    return booking


def _existing_completed_payment(db: Session, booking_id: str) -> bool:
    return db.query(Payment).filter(
        Payment.booking_id == booking_id,
        Payment.status == "completed",
    ).first() is not None


# ── POST /api/payments/initiate ────────────────────────────────────────────────

@router.post("/initiate", response_model=PaymentInitiateResponse)
def initiate_payment(
    body: PaymentInitiateRequest,
    db: DbSession,
    current_user=Depends(get_current_user),
):
    booking = _get_booking_or_404(db, body.booking_id, current_user.id)

    if _existing_completed_payment(db, body.booking_id):
        raise HTTPException(status_code=400, detail="Booking already paid")

    now = _now()
    payment_id = str(uuid.uuid4())
    tx_ref = f"KRV-{payment_id[:8].upper()}"

    if body.method == "card":
        if not settings.paystack_secret_key or settings.paystack_secret_key.startswith("sk_test_REPLACE"):
            raise HTTPException(status_code=503, detail="Paystack is not configured")

        amount_ugx = _get_booking_amount_ugx(db, booking)

        try:
            ps_resp = paystack_service.initialize_transaction(
                amount_ugx=amount_ugx,
                email=current_user.email,
                reference=tx_ref,
                booking_id=booking.id,
                callback_url=settings.payment_redirect_url,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Paystack error: {exc}")

        if not ps_resp.get("status"):
            raise HTTPException(status_code=502, detail=ps_resp.get("message", "Paystack initiation failed"))

        ps_data = ps_resp.get("data", {})

        payment = Payment(
            id=payment_id,
            booking_id=booking.id,
            payer_id=current_user.id,
            amount_ugx=amount_ugx,
            currency="UGX",
            payment_method="card",
            payment_channel="paystack",
            gateway_reference=tx_ref,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        db.add(payment)
        db.commit()

        return PaymentInitiateResponse(
            payment_id=payment_id,
            method="card",
            status="pending",
            authorization_url=ps_data.get("authorization_url"),
            access_code=ps_data.get("access_code"),
            reference=tx_ref,
            public_key=settings.paystack_public_key,
        )

    # Mobile money (Flutterwave)
    if not body.phone_number or not body.network:
        raise HTTPException(status_code=422, detail="phone_number and network are required for mobile_money")

    if not settings.flutterwave_secret_key or settings.flutterwave_secret_key.startswith("FLWSECK_TEST-REPLACE"):
        raise HTTPException(status_code=503, detail="Flutterwave is not configured")

    amount_ugx = _get_booking_amount_ugx(db, booking)

    try:
        flw_resp = flutterwave_service.charge_mobile_money(
            tx_ref=tx_ref,
            amount_ugx=amount_ugx,
            phone_number=body.phone_number,
            network=body.network,
            customer_email=current_user.email,
            customer_name=current_user.full_name,
            booking_id=booking.id,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Flutterwave error: {exc}")

    flw_status = flw_resp.get("status", "error")
    if flw_status != "success":
        raise HTTPException(status_code=502, detail=flw_resp.get("message", "Mobile money initiation failed"))

    payment = Payment(
        id=payment_id,
        booking_id=booking.id,
        payer_id=current_user.id,
        amount_ugx=amount_ugx,
        currency="UGX",
        payment_method="mobile_money",
        payment_channel=body.network,
        gateway_reference=tx_ref,   # store our tx_ref for verify_by_reference lookup
        phone_number=body.phone_number,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.commit()

    return PaymentInitiateResponse(
        payment_id=payment_id,
        method="mobile_money",
        status="pending",
        flw_ref=tx_ref,
        message="Approve the payment prompt on your phone",
    )


# ── POST /api/payments/{payment_id}/verify ────────────────────────────────────

@router.post("/{payment_id}/verify")
def verify_payment(
    payment_id: str,
    db: DbSession,
    current_user=Depends(get_current_user),
):
    """
    Manually pull the current status from Stripe or Flutterwave and sync it to
    the database.  Use this during development/testing instead of setting up
    webhook endpoints.

    Returns the updated payment status.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.payer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your payment")

    if payment.status == "completed":
        return {"payment_id": payment_id, "status": "completed", "message": "Already completed"}

    gateway_ref = payment.gateway_reference

    # ── Paystack card payment ──────────────────────────────────────────────────
    if payment.payment_channel == "paystack":
        try:
            resp = paystack_service.verify_transaction(gateway_ref)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Paystack error: {exc}")

        ps_data = resp.get("data", {})
        ps_status = ps_data.get("status", "pending")  # success | failed | abandoned | pending

        if ps_status == "success":
            _mark_payment_completed_by_ref(
                db, gateway_ref, receipt_url=None,
                paid_amount_ugx=ps_data.get("amount"),
            )
            return {"payment_id": payment_id, "status": "completed", "gateway_status": ps_status}

        if ps_status in ("failed", "abandoned"):
            _mark_payment_failed_by_ref(db, gateway_ref)
            return {"payment_id": payment_id, "status": "failed", "gateway_status": ps_status}

        return {"payment_id": payment_id, "status": "pending", "gateway_status": ps_status}

    # ── Flutterwave mobile money ───────────────────────────────────────────────
    if payment.payment_channel in ("MTN_UGANDA", "AIRTEL_UGANDA"):
        try:
            resp = flutterwave_service.verify_transaction(gateway_ref)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Flutterwave error: {exc}")

        tx_data = resp.get("data", {})
        flw_status = tx_data.get("status", "pending")  # successful | failed | pending

        if flw_status == "successful":
            _mark_payment_completed_by_ref(
                db, gateway_ref, receipt_url=None,
                paid_amount_ugx=tx_data.get("amount"),
            )
            return {"payment_id": payment_id, "status": "completed", "gateway_status": flw_status}

        if flw_status == "failed":
            _mark_payment_failed_by_ref(db, gateway_ref)
            return {"payment_id": payment_id, "status": "failed", "gateway_status": flw_status}

        return {"payment_id": payment_id, "status": "pending", "gateway_status": flw_status}

    raise HTTPException(status_code=400, detail=f"Unknown payment channel: {payment.payment_channel}")


# ── POST /api/payments/webhook/paystack ───────────────────────────────────────

@router.post("/webhook/paystack", include_in_schema=False)
async def paystack_webhook(
    request: Request,
    db: DbSession,
    x_paystack_signature: str = Header(None, alias="x-paystack-signature"),
):
    """
    Paystack signs webhooks with HMAC-SHA512 using your secret key.
    No separate webhook secret is needed — the secret key is enough.
    """
    payload = await request.body()

    if not x_paystack_signature or not paystack_service.verify_webhook_signature(payload, x_paystack_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    data = json.loads(payload)
    event = data.get("event", "")
    tx_data = data.get("data", {})

    if event == "charge.success":
        reference = tx_data.get("reference")
        amount = tx_data.get("amount")
        _mark_payment_completed_by_ref(db, reference, receipt_url=None, paid_amount_ugx=amount)

    return {"received": True}


# ── POST /api/payments/webhook/flutterwave ─────────────────────────────────────

@router.post("/webhook/flutterwave", include_in_schema=False)
async def flutterwave_webhook(
    request: Request,
    db: DbSession,
    verif_hash: str = Header(None, alias="verif-hash"),
):
    payload = await request.body()

    if settings.flutterwave_secret_key and verif_hash:
        if not flutterwave_service.verify_webhook_signature(payload, verif_hash):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    data = json.loads(payload)
    event_type = data.get("event", "")
    tx_data = data.get("data", {})

    if event_type == "charge.completed" and tx_data.get("status") == "successful":
        tx_ref = tx_data.get("tx_ref")
        amount = tx_data.get("amount")
        _mark_payment_completed_by_ref(db, tx_ref, receipt_url=None, paid_amount_ugx=amount)

    elif event_type == "charge.completed" and tx_data.get("status") == "failed":
        tx_ref = tx_data.get("tx_ref")
        _mark_payment_failed_by_ref(db, tx_ref)

    return {"received": True}


# ── GET /api/payments/{booking_id}/status ─────────────────────────────────────

@router.get("/{booking_id}/status")
def payment_status(
    booking_id: str,
    db: DbSession,
    current_user=Depends(get_current_user),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your booking")

    payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    if not payment:
        return {"booking_id": booking_id, "payment_status": "no_payment"}

    return {
        "booking_id": booking_id,
        "payment_id": payment.id,
        "payment_status": payment.status,
        "method": payment.payment_method,
        "channel": payment.payment_channel,
        "amount_ugx": payment.amount_ugx,
        "amount_usd": str(payment.amount_usd) if payment.amount_usd else None,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "receipt_url": payment.receipt_url,
    }


# ── GET /api/payments/callback (Flutterwave redirect) ─────────────────────────

@router.get("/callback")
def payment_callback(
    status: str = "unknown",
    tx_ref: str = "",
    transaction_id: str = "",
    db: DbSession = None,
):
    """
    Flutterwave redirects here after hosted checkout.
    Re-verify the transaction and update DB if needed.
    """
    if status == "successful" and transaction_id:
        try:
            verify_resp = flutterwave_service.verify_transaction(transaction_id)
            tx_data = verify_resp.get("data", {})
            if tx_data.get("status") == "successful":
                flw_ref = tx_data.get("flw_ref")
                _mark_payment_completed_by_ref(db, flw_ref, receipt_url=None)
        except Exception:
            pass  # webhook will handle it if redirect fails

    return {"status": status, "tx_ref": tx_ref, "message": "Payment processed"}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _get_booking_amount_ugx(db: Session, booking: Booking) -> int:
    """
    Try to find an existing pending payment amount, else raise 422.
    The booking amount in UGX must come from the pricing engine (Phase 7).
    For now, require caller to have previously stored a pending payment or
    look it up from a vehicle daily rate × total_days.
    """
    from app.models.vehicle import Vehicle

    vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=422, detail="Vehicle not found for booking")

    total_days = booking.total_days or 1
    if vehicle.base_daily_rate_ugx is None:
        raise HTTPException(status_code=422, detail="Vehicle has no price set")

    return int(vehicle.base_daily_rate_ugx) * total_days



COMMISSION_RATE    = 0.17
OWNER_DEPOSIT_RATE = 0.30


def _mark_payment_completed_by_ref(
    db: Session,
    gateway_ref: str,
    receipt_url: str | None,
    paid_amount_ugx: int | None = None,
):
    payment = db.query(Payment).filter(Payment.gateway_reference == gateway_ref).first()
    if not payment:
        return
    if payment.status == "completed":
        return
    now = _now()
    payment.status = "completed"
    payment.paid_at = now
    payment.updated_at = now
    if receipt_url:
        payment.receipt_url = receipt_url
    if paid_amount_ugx:
        payment.amount_ugx = int(paid_amount_ugx)

    # Confirm booking
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
    if booking and booking.status != "confirmed":
        booking.status = "confirmed"
        booking.updated_at = now

    # Commission + 30 % deposit payout
    if booking:
        vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
        if vehicle:
            vehicle_subtotal_ugx = (booking.total_days or 1) * int(vehicle.base_daily_rate_ugx)
            commission_ugx = int(vehicle_subtotal_ugx * COMMISSION_RATE)
            owner_net_ugx  = vehicle_subtotal_ugx - commission_ugx
            deposit_ugx    = int(owner_net_ugx * OWNER_DEPOSIT_RATE)

            existing = db.query(Commission).filter(Commission.booking_id == booking.id).first()
            if not existing:
                db.add(Commission(
                    id=str(uuid.uuid4()),
                    booking_id=booking.id,
                    payment_id=payment.id,
                    gross_amount_ugx=vehicle_subtotal_ugx,
                    commission_rate=COMMISSION_RATE,
                    commission_ugx=commission_ugx,
                    owner_payout_ugx=owner_net_ugx,
                    calculated_at=now,
                ))
                db.add(Payout(
                    id=str(uuid.uuid4()),
                    owner_id=vehicle.owner_id,
                    booking_ids=booking.id,
                    total_amount_ugx=deposit_ugx,
                    payout_method="pending",
                    status="pending",
                    requested_at=now,
                ))

    db.commit()


def _mark_payment_failed_by_ref(db: Session, gateway_ref: str):
    payment = db.query(Payment).filter(Payment.gateway_reference == gateway_ref).first()
    if not payment:
        return
    payment.status = "failed"
    payment.updated_at = _now()
    db.commit()
