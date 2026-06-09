import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Booking, Commission, Payment, Payout, Vehicle
from app.models.vehicle import VehiclePhoto
from app.schemas.booking import BookingListItem, BookingPaymentResponse, BookingRequest, VehicleSnapshot
from app.services.stripe_service import create_payment_intent, get_payment_intent

router = APIRouter(prefix="/bookings", tags=["bookings"])

_admin = require_role("admin")
_any_auth = get_current_user

RATES_UGX_PER_USD  = 3700
EUR_TO_USD         = 1.08          # approximate fixed rate
SERVICE_FEE_EUR    = 2.50          # Karivari flat service fee per booking
MAINTENANCE_FEE_EUR = 17.00        # Karivari maintenance fee added on top of owner rate
PLATFORM_FEE_USD   = round((SERVICE_FEE_EUR + MAINTENANCE_FEE_EUR) * EUR_TO_USD, 2)
COMMISSION_RATE    = 0.17          # 17 % Karivari commission on vehicle subtotal
OWNER_DEPOSIT_RATE = 0.30         # 30 % of owner payout released immediately on payment


# POST /api/bookings — any authenticated user creates a booking + Stripe PaymentIntent
@router.post("/", response_model=BookingPaymentResponse)
def create_booking(
    payload: BookingRequest,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if vehicle.status != "verified":
        raise HTTPException(status_code=400, detail="Vehicle is not available for booking")
    if vehicle.owner_id == current_user.id:
        raise HTTPException(status_code=403, detail="Vehicle owners cannot book their own vehicle")

    try:
        start_dt = datetime.strptime(payload.pickup_date, "%Y-%m-%d")
        end_dt   = datetime.strptime(payload.return_date,  "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format — use YYYY-MM-DD")

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    if start_dt < today:
        raise HTTPException(status_code=400, detail="Pickup date cannot be in the past")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="Return date must be after pickup date")

    total_days = max(1, (end_dt - start_dt).days)

    # Server-side rate calculation
    daily_ugx      = vehicle.base_daily_rate_ugx
    daily_usd      = daily_ugx / RATES_UGX_PER_USD
    vehicle_usd    = round(daily_usd * total_days, 2)      # owner subtotal
    amount_usd     = round(vehicle_usd + PLATFORM_FEE_USD, 2)  # customer pays this (owner rate + €2.50 service + €17 maintenance)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking_id  = str(uuid.uuid4())
    booking_ref = f"KV-{booking_id[:8].upper()}"

    booking = Booking(
        id=booking_id,
        booking_reference=booking_ref,
        customer_id=current_user.id,
        vehicle_id=payload.vehicle_id,
        booking_type="with_driver",
        trip_type="daily_rental",
        pickup_location=payload.pickup_location,
        dropoff_location=payload.dropoff_location,
        start_datetime=start_dt,
        end_datetime=end_dt,
        total_days=total_days,
        passenger_count=payload.passenger_count,
        special_requests=payload.special_requests,
        status="pending_payment",
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    db.flush()

    # Create Stripe PaymentIntent
    amount_cents = int(amount_usd * 100)
    try:
        intent = create_payment_intent(
            amount_usd_cents=amount_cents,
            booking_id=booking_id,
            customer_email=current_user.email,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Payment service error: {exc}")

    payment = Payment(
        id=str(uuid.uuid4()),
        booking_id=booking_id,
        payer_id=current_user.id,
        amount_ugx=int(amount_usd * RATES_UGX_PER_USD),
        amount_usd=amount_usd,
        currency="USD",
        payment_method="card",
        payment_channel="stripe",
        gateway_reference=intent["payment_intent_id"],
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.commit()

    return BookingPaymentResponse(
        booking_id=booking_id,
        booking_reference=booking_ref,
        client_secret=intent["client_secret"],
        amount_usd=amount_usd,
    )


# POST /api/bookings/{id}/confirm-payment — called by frontend after Stripe succeeds
@router.post("/{booking_id}/confirm-payment")
def confirm_payment(
    booking_id: str,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "pending_payment":
        return {"status": booking.status, "booking_reference": booking.booking_reference}

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    try:
        intent = get_payment_intent(payment.gateway_reference)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not verify payment: {exc}")

    if intent.status != "succeeded":
        raise HTTPException(status_code=402, detail=f"Payment not completed (status: {intent.status})")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking.status     = "confirmed"
    booking.updated_at = now
    payment.status     = "completed"
    payment.paid_at    = now
    payment.updated_at = now

    # --- Commission & owner deposit ---
    # Commission is on the vehicle subtotal only — platform fees (€2.50 + €17) go entirely to Karivari
    vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
    vehicle_subtotal_ugx = booking.total_days * vehicle.base_daily_rate_ugx
    gross_ugx      = vehicle_subtotal_ugx
    commission_ugx = int(gross_ugx * COMMISSION_RATE)
    owner_net_ugx  = gross_ugx - commission_ugx
    deposit_ugx    = int(owner_net_ugx * OWNER_DEPOSIT_RATE)

    commission = Commission(
        id=str(uuid.uuid4()),
        booking_id=booking_id,
        payment_id=payment.id,
        gross_amount_ugx=gross_ugx,
        commission_rate=COMMISSION_RATE,
        commission_ugx=commission_ugx,
        owner_payout_ugx=owner_net_ugx,
        calculated_at=now,
    )
    db.add(commission)

    deposit_payout = Payout(
        id=str(uuid.uuid4()),
        owner_id=vehicle.owner_id,
        booking_ids=booking_id,
        total_amount_ugx=deposit_ugx,
        payout_method="pending",
        status="pending",
        requested_at=now,
    )
    db.add(deposit_payout)
    db.commit()

    return {"status": "confirmed", "booking_reference": booking.booking_reference}


# GET /api/bookings/owner — bookings on the current owner's vehicles (must come before /{booking_id})
_owner = require_role("owner")


@router.get("/owner", response_model=List[BookingListItem])
def list_owner_bookings(
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(_owner),
):
    owned_ids = [v.id for v in db.query(Vehicle.id).filter(Vehicle.owner_id == current_user.id).all()]
    if not owned_ids:
        return []

    query = db.query(Booking).filter(Booking.vehicle_id.in_(owned_ids))
    if status:
        query = query.filter(Booking.status == status)
    bookings = query.order_by(Booking.created_at.desc()).all()

    from app.models.user import User

    result = []
    for b in bookings:
        payment = (
            db.query(Payment)
            .filter(Payment.booking_id == b.id)
            .order_by(Payment.created_at.desc())
            .first()
        )
        vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()
        customer = db.query(User).filter(User.id == b.customer_id).first()

        vehicle_snapshot = None
        if vehicle:
            photo = (
                db.query(VehiclePhoto)
                .filter(VehiclePhoto.vehicle_id == vehicle.id, VehiclePhoto.is_primary.is_(True))
                .first()
                or db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle.id).first()
            )
            vehicle_snapshot = VehicleSnapshot(
                id=vehicle.id,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                vehicle_type=vehicle.vehicle_type,
                base_daily_rate_ugx=int(vehicle.base_daily_rate_ugx),
                primary_photo_url=photo.photo_url if photo else None,
            )

        item = BookingListItem(
            id=b.id,
            booking_reference=b.booking_reference,
            vehicle_id=b.vehicle_id,
            booking_type=b.booking_type,
            pickup_location=b.pickup_location,
            dropoff_location=b.dropoff_location,
            start_datetime=b.start_datetime,
            end_datetime=b.end_datetime,
            total_days=b.total_days,
            passenger_count=b.passenger_count,
            status=b.status,
            created_at=b.created_at,
            amount_ugx=int(payment.amount_ugx) if payment else None,
            amount_usd=float(payment.amount_usd) if payment and payment.amount_usd else None,
            vehicle=vehicle_snapshot,
        )
        # attach customer name as extra field via __dict__
        item.__dict__['customer_name'] = customer.full_name if customer else '—'
        result.append(item)

    return result


# GET /api/bookings — customer's own bookings with vehicle + payment data
@router.get("/", response_model=List[BookingListItem])
def list_bookings(current_user=Depends(_any_auth), db: Session = Depends(get_db)):
    bookings = (
        db.query(Booking)
        .filter(Booking.customer_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    result = []
    for b in bookings:
        payment = (
            db.query(Payment)
            .filter(Payment.booking_id == b.id)
            .order_by(Payment.created_at.desc())
            .first()
        )
        vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()

        vehicle_snapshot = None
        if vehicle:
            photo = (
                db.query(VehiclePhoto)
                .filter(VehiclePhoto.vehicle_id == vehicle.id, VehiclePhoto.is_primary.is_(True))
                .first()
                or db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle.id).first()
            )
            vehicle_snapshot = VehicleSnapshot(
                id=vehicle.id,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                vehicle_type=vehicle.vehicle_type,
                base_daily_rate_ugx=int(vehicle.base_daily_rate_ugx),
                primary_photo_url=photo.photo_url if photo else None,
            )

        result.append(BookingListItem(
            id=b.id,
            booking_reference=b.booking_reference,
            vehicle_id=b.vehicle_id,
            booking_type=b.booking_type,
            pickup_location=b.pickup_location,
            dropoff_location=b.dropoff_location,
            start_datetime=b.start_datetime,
            end_datetime=b.end_datetime,
            total_days=b.total_days,
            passenger_count=b.passenger_count,
            status=b.status,
            created_at=b.created_at,
            amount_ugx=int(payment.amount_ugx) if payment else None,
            amount_usd=float(payment.amount_usd) if payment and payment.amount_usd else None,
            vehicle=vehicle_snapshot,
        ))

    return result


# GET /api/bookings/{id}
@router.get("/{booking_id}", response_model=BookingListItem)
def get_booking(booking_id: str, current_user=Depends(_any_auth), db: Session = Depends(get_db)):
    b = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id,
    ).first()
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = (
        db.query(Payment)
        .filter(Payment.booking_id == b.id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    vehicle = db.query(Vehicle).filter(Vehicle.id == b.vehicle_id).first()

    vehicle_snapshot = None
    if vehicle:
        photo = (
            db.query(VehiclePhoto)
            .filter(VehiclePhoto.vehicle_id == vehicle.id, VehiclePhoto.is_primary.is_(True))
            .first()
            or db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle.id).first()
        )
        vehicle_snapshot = VehicleSnapshot(
            id=vehicle.id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            vehicle_type=vehicle.vehicle_type,
            base_daily_rate_ugx=int(vehicle.base_daily_rate_ugx),
            primary_photo_url=photo.photo_url if photo else None,
        )

    return BookingListItem(
        id=b.id,
        booking_reference=b.booking_reference,
        vehicle_id=b.vehicle_id,
        booking_type=b.booking_type,
        pickup_location=b.pickup_location,
        dropoff_location=b.dropoff_location,
        start_datetime=b.start_datetime,
        end_datetime=b.end_datetime,
        total_days=b.total_days,
        passenger_count=b.passenger_count,
        status=b.status,
        created_at=b.created_at,
        amount_ugx=int(payment.amount_ugx) if payment else None,
        amount_usd=float(payment.amount_usd) if payment and payment.amount_usd else None,
        vehicle=vehicle_snapshot,
    )


class CancelRequest(BaseModel):
    cancellation_reason: str = ""


# PATCH /api/bookings/{id}/cancel
@router.patch("/{booking_id}/cancel")
def cancel_booking(
    booking_id: str,
    payload: CancelRequest = CancelRequest(),
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    CANCELLABLE = {"pending_payment", "pending", "confirmed"}
    if booking.status not in CANCELLABLE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a booking with status '{booking.status}'",
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking.status = "cancelled"
    booking.cancelled_by = current_user.id
    booking.cancelled_at = now
    booking.cancellation_reason = payload.cancellation_reason or None
    booking.updated_at = now
    db.commit()

    return {"status": "cancelled", "booking_reference": booking.booking_reference}


# POST /api/bookings/{id}/review — handled by /api/reviews/ router
