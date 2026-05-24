import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Booking, Payment, Vehicle
from app.models.vehicle import VehiclePhoto
from app.schemas.booking import BookingListItem, BookingPaymentResponse, BookingRequest, VehicleSnapshot
from app.services.stripe_service import create_payment_intent, get_payment_intent

router = APIRouter(prefix="/bookings", tags=["bookings"])

_driver = require_role("driver")
_admin = require_role("admin")
_any_auth = get_current_user

RATES_UGX_PER_USD = 3700
SERVICE_FEE_USD = 15.0


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

    try:
        start_dt = datetime.strptime(payload.pickup_date, "%Y-%m-%d")
        end_dt   = datetime.strptime(payload.return_date,  "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format — use YYYY-MM-DD")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="Return date must be after pickup date")

    total_days = max(1, (end_dt - start_dt).days)

    # Server-side rate calculation
    if payload.booking_type == "with_driver" and vehicle.rate_with_driver_ugx:
        daily_ugx = vehicle.rate_with_driver_ugx
    else:
        daily_ugx = vehicle.base_daily_rate_ugx
    daily_usd = daily_ugx / RATES_UGX_PER_USD
    amount_usd = round(daily_usd * total_days + SERVICE_FEE_USD, 2)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking_id  = str(uuid.uuid4())
    booking_ref = f"KV-{booking_id[:8].upper()}"

    booking = Booking(
        id=booking_id,
        booking_reference=booking_ref,
        customer_id=current_user.id,
        vehicle_id=payload.vehicle_id,
        booking_type=payload.booking_type,
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
    booking.status    = "confirmed"
    booking.updated_at = now
    payment.status    = "completed"
    payment.paid_at   = now
    payment.updated_at = now
    db.commit()

    return {"status": "confirmed", "booking_reference": booking.booking_reference}


# GET /api/bookings/owner — bookings on the current owner's vehicles
@router.get("/owner", response_model=List[BookingListItem])
def list_owner_bookings(
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(_any_auth),
):
    # Get all vehicle IDs owned by this user
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


class AssignDriverRequest(BaseModel):
    driver_profile_id: str


# PATCH /api/bookings/{id}/assign-driver
@router.patch("/{booking_id}/assign-driver")
def assign_driver(
    booking_id: str,
    payload: AssignDriverRequest,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.driver import DriverProfile

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in {"confirmed", "pending"}:
        raise HTTPException(status_code=400, detail=f"Cannot assign driver to booking with status '{booking.status}'")

    driver = db.query(DriverProfile).filter(DriverProfile.id == payload.driver_profile_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    if driver.verification_status != "approved":
        raise HTTPException(status_code=400, detail="Driver is not yet approved")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking.driver_id = payload.driver_profile_id
    booking.assigned_by_admin = current_user.id
    booking.updated_at = now
    db.commit()

    return {"status": booking.status, "booking_reference": booking.booking_reference, "driver_id": driver.id}


class RespondRequest(BaseModel):
    action: str  # "accept" | "reject"


# PATCH /api/bookings/{id}/respond
@router.patch("/{booking_id}/respond")
def respond_to_assignment(
    booking_id: str,
    payload: RespondRequest,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    from app.models.driver import DriverProfile

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.driver_id == profile.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not assigned to you")

    if payload.action not in {"accept", "reject"}:
        raise HTTPException(status_code=400, detail="action must be 'accept' or 'reject'")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.action == "reject":
        booking.driver_id = None
        booking.updated_at = now

    db.commit()
    return {"action": payload.action, "booking_reference": booking.booking_reference}


# PATCH /api/bookings/{id}/start
@router.patch("/{booking_id}/start")
def start_trip(
    booking_id: str,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    from app.models.driver import DriverProfile

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.driver_id == profile.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not assigned to you")
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail=f"Trip cannot be started from status '{booking.status}'")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking.status = "in_progress"
    booking.actual_start_at = now
    booking.updated_at = now
    db.commit()

    return {"status": "in_progress", "booking_reference": booking.booking_reference}


# PATCH /api/bookings/{id}/complete
@router.patch("/{booking_id}/complete")
def complete_trip(
    booking_id: str,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    from app.models.driver import DriverProfile

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.driver_id == profile.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not assigned to you")
    if booking.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Trip cannot be completed from status '{booking.status}'")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booking.status = "completed"
    booking.actual_end_at = now
    booking.updated_at = now

    profile.total_trips = (profile.total_trips or 0) + 1
    profile.updated_at = now

    db.commit()

    return {"status": "completed", "booking_reference": booking.booking_reference}


# POST /api/bookings/{id}/review — handled by /api/reviews/ router
