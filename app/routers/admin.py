import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import AuditLog, Booking, Commission, Payment, Payout, User, Vehicle
from app.models.kyc import RefreshToken
from app.schemas.vehicle import VehicleRead, VerificationDecision
from app.security import create_access_token, create_refresh_token, hash_password
from app.services.notifications import create_notification

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_role("admin")

_DEV_ADMIN_EMAIL = "admin@karivari.ug"
_DEV_ADMIN_NAME = "Admin"


# ── POST /api/admin/dev-signin ────────────────────────────────────────────────


@router.post("/dev-signin", include_in_schema=False)
def dev_signin(db: Session = Depends(get_db)):
    """
    Development shortcut: auto-provision an admin account and return a token.
    No credentials required. Remove or gate behind a feature flag before going live.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    user = db.query(User).filter(User.email == _DEV_ADMIN_EMAIL).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            full_name=_DEV_ADMIN_NAME,
            email=_DEV_ADMIN_EMAIL,
            phone_number="+000000000000",
            password_hash=hash_password("Admin1234!"),
            role="admin",
            account_type="individual",
            preferred_language="en",
            is_verified=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.role)
    refresh_raw = create_refresh_token(user.id)

    db.add(
        RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_password(refresh_raw),
            expires_at=now + timedelta(days=14),
            created_at=now,
        )
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_raw,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "full_name": user.full_name,
    }


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _write_audit(
    db: Session,
    *,
    admin_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
):
    db.add(
        AuditLog(
            id=str(uuid.uuid4()),
            actor_id=admin_id,
            actor_role="admin",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_value=details,
            occurred_at=_now(),
        )
    )


# ---------------------------------------------------------------------------
# Verifications — Vehicles
# ---------------------------------------------------------------------------


@router.get("/stats")
def admin_stats(current_user=Depends(_admin), db: Session = Depends(get_db)):
    """Live platform-wide counts for the admin dashboard."""
    from sqlalchemy import func

    from app.models.dispute import Dispute

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_vehicles = (
        db.query(func.count(Vehicle.id)).filter(Vehicle.status == "verified").scalar()
        or 0
    )
    pending_verifications = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.status == "pending_review")
        .scalar()
        or 0
    )
    open_disputes = (
        db.query(func.count(Dispute.id)).filter(Dispute.status == "open").scalar() or 0
    )

    return {
        "total_users": total_users,
        "active_vehicles": active_vehicles,
        "pending_verifications": pending_verifications,
        "open_disputes": open_disputes,
    }


@router.get("/verifications/pending")
def list_pending_verifications(
    type: Optional[str] = Query("vehicle", pattern="^(vehicle|owner)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    if type == "vehicle":
        return (
            db.query(Vehicle)
            .filter(Vehicle.status == "pending")
            .offset(offset)
            .limit(page_size)
            .all()
        )

    # owner stub — Phase TBD
    raise HTTPException(
        status_code=501, detail="Pending owner verifications not yet implemented"
    )


@router.patch("/verifications/{vehicle_id}/approve", response_model=VehicleRead)
def approve_vehicle(
    vehicle_id: str,
    payload: VerificationDecision = VerificationDecision(),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if v.status != "pending":
        raise HTTPException(
            status_code=400, detail=f"Vehicle is '{v.status}', not pending"
        )

    v.status = "verified"
    v.rejection_reason = None
    v.updated_at = _now()
    db.add(v)

    _write_audit(
        db,
        admin_id=current_user.id,
        action="verify_vehicle",
        entity_type="vehicle",
        entity_id=vehicle_id,
        details={"note": payload.reason},
    )

    create_notification(
        db,
        user_id=v.owner_id,
        notification_type="verification_approved",
        title="Your vehicle has been verified!",
        body=f"Your {v.make} {v.model} ({v.registration_plate}) is now live on Karivari.",
        related_entity_type="vehicle",
        related_entity_id=vehicle_id,
    )

    db.commit()
    db.refresh(v)
    return v


@router.patch("/verifications/{vehicle_id}/reject", response_model=VehicleRead)
def reject_vehicle(
    vehicle_id: str,
    payload: VerificationDecision,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    if not payload.reason:
        raise HTTPException(
            status_code=422, detail="A reason is required when rejecting a vehicle"
        )

    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if v.status not in ("pending", "verified"):
        raise HTTPException(
            status_code=400, detail=f"Cannot reject a vehicle with status '{v.status}'"
        )

    v.status = "rejected"
    v.rejection_reason = payload.reason
    v.updated_at = _now()
    db.add(v)

    _write_audit(
        db,
        admin_id=current_user.id,
        action="reject_vehicle",
        entity_type="vehicle",
        entity_id=vehicle_id,
        details={"reason": payload.reason},
    )

    create_notification(
        db,
        user_id=v.owner_id,
        notification_type="verification_rejected",
        title="Vehicle verification unsuccessful",
        body=f"Your {v.make} {v.model} was not approved. Reason: {payload.reason}",
        related_entity_type="vehicle",
        related_entity_id=vehicle_id,
    )

    db.commit()
    db.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Tourist KYC (Phase 7)
# ---------------------------------------------------------------------------


@router.get("/kyc/manual-review")
def list_kyc_manual_review(
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.user import UserIdentityVerification

    records = (
        db.query(UserIdentityVerification)
        .filter(UserIdentityVerification.verification_status == "pending")
        .order_by(UserIdentityVerification.submitted_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "document_type": r.document_type,
            "document_number": r.document_number,
            "document_front_url": r.document_front_url,
            "document_back_url": r.document_back_url,
            "selfie_url": r.selfie_url,
            "submitted_at": r.submitted_at,
        }
        for r in records
    ]


class KYCDecision(BaseModel):
    reason: Optional[str] = None


@router.patch("/kyc/{record_id}/approve")
def approve_kyc(
    record_id: str,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.user import UserIdentityVerification

    record = (
        db.query(UserIdentityVerification)
        .filter(UserIdentityVerification.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")

    record.verification_status = "approved"
    record.reviewed_by = current_user.id
    record.reviewed_at = _now()
    record.rejection_reason = None
    db.commit()

    create_notification(
        db,
        user_id=record.user_id,
        notification_type="kyc_approved",
        title="Identity verification approved",
        body="Your identity has been verified on Kari Vari Uganda.",
        related_entity_type="kyc",
        related_entity_id=record.id,
    )

    _write_audit(
        db,
        admin_id=current_user.id,
        action="approve_kyc",
        entity_type="user_identity_verification",
        entity_id=record.id,
    )
    db.commit()
    return {"status": "approved", "record_id": record.id}


@router.patch("/kyc/{record_id}/reject")
def reject_kyc(
    record_id: str,
    payload: KYCDecision,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.user import UserIdentityVerification

    if not payload.reason:
        raise HTTPException(
            status_code=422,
            detail="A reason is required when rejecting a KYC submission",
        )

    record = (
        db.query(UserIdentityVerification)
        .filter(UserIdentityVerification.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="KYC record not found")

    record.verification_status = "rejected"
    record.reviewed_by = current_user.id
    record.reviewed_at = _now()
    record.rejection_reason = payload.reason
    db.commit()

    create_notification(
        db,
        user_id=record.user_id,
        notification_type="kyc_rejected",
        title="Identity verification unsuccessful",
        body=f"Your document was not approved. Reason: {payload.reason}",
        related_entity_type="kyc",
        related_entity_id=record.id,
    )

    _write_audit(
        db,
        admin_id=current_user.id,
        action="reject_kyc",
        entity_type="user_identity_verification",
        entity_id=record.id,
        details={"reason": payload.reason},
    )
    db.commit()
    return {"status": "rejected", "record_id": record.id}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users")
def list_users(
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if search:
        q = q.filter(
            (User.full_name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    offset = (page - 1) * page_size
    users = q.offset(offset).limit(page_size).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    u.is_active = not u.is_active
    u.updated_at = _now()
    db.add(u)

    _write_audit(
        db,
        admin_id=current_user.id,
        action="suspend_user" if not u.is_active else "unsuspend_user",
        entity_type="user",
        entity_id=user_id,
    )

    db.commit()
    return {"id": user_id, "is_active": u.is_active}


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------


@router.get("/bookings")
def list_all_bookings(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models import Booking, Payment

    q = db.query(Booking)
    if status_filter:
        q = q.filter(Booking.status == status_filter)
    total = q.count()
    bookings = (
        q.order_by(Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for b in bookings:
        customer = db.query(User).filter(User.id == b.customer_id).first()
        payment = (
            db.query(Payment)
            .filter(Payment.booking_id == b.id)
            .order_by(Payment.created_at.desc())
            .first()
        )
        result.append(
            {
                "id": b.id,
                "booking_reference": b.booking_reference,
                "status": b.status,
                "booking_type": b.booking_type,
                "customer_name": customer.full_name if customer else None,
                "customer_email": customer.email if customer else None,
                "vehicle_id": b.vehicle_id,
                "start_datetime": b.start_datetime,
                "end_datetime": b.end_datetime,
                "total_days": b.total_days,
                "amount_usd": float(payment.amount_usd)
                if payment and payment.amount_usd
                else None,
                "created_at": b.created_at,
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "bookings": result}


class BookingStatusOverride(BaseModel):
    status: str
    reason: Optional[str] = None


@router.patch("/bookings/{booking_id}/override-status")
def override_booking_status(
    booking_id: str,
    payload: BookingStatusOverride,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models import Booking

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    VALID_STATUSES = {
        "pending_payment",
        "pending",
        "confirmed",
        "in_progress",
        "completed",
        "cancelled",
    }
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of {VALID_STATUSES}"
        )

    old_status = booking.status
    booking.status = payload.status
    booking.updated_at = _now()
    db.commit()

    # On trip completion, release the remaining 70 % payout to the owner
    if payload.status == "completed" and old_status != "completed":
        commission = (
            db.query(Commission).filter(Commission.booking_id == booking_id).first()
        )
        if commission:
            deposit = db.query(Payout).filter(Payout.booking_ids == booking_id).first()
            deposit_ugx = deposit.total_amount_ugx if deposit else 0
            remainder_ugx = commission.owner_payout_ugx - deposit_ugx
            if remainder_ugx > 0:
                vehicle = (
                    db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
                )
                remainder_payout = Payout(
                    id=str(uuid.uuid4()),
                    owner_id=vehicle.owner_id,
                    booking_ids=booking_id,
                    total_amount_ugx=remainder_ugx,
                    payout_method="pending",
                    status="pending",
                    requested_at=_now(),
                )
                db.add(remainder_payout)
                db.commit()

    _write_audit(
        db,
        admin_id=current_user.id,
        action="override_booking_status",
        entity_type="booking",
        entity_id=booking_id,
        details={
            "old_status": old_status,
            "new_status": payload.status,
            "reason": payload.reason,
        },
    )
    db.commit()

    return {"booking_id": booking_id, "status": payload.status}


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------


@router.get("/disputes")
def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.dispute import Dispute

    q = db.query(Dispute)
    if status_filter:
        q = q.filter(Dispute.status == status_filter)
    total = q.count()
    disputes = (
        q.order_by(Dispute.opened_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for d in disputes:
        raiser = db.query(User).filter(User.id == d.raised_by).first()
        result.append(
            {
                "id": d.id,
                "booking_id": d.booking_id,
                "dispute_type": d.dispute_type,
                "description": d.description,
                "status": d.status,
                "raised_by_name": raiser.full_name if raiser else None,
                "resolution_notes": d.resolution_notes,
                "refund_issued": d.refund_issued,
                "opened_at": d.opened_at,
                "resolved_at": d.resolved_at,
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "disputes": result}


class DisputeResolve(BaseModel):
    resolution_notes: str
    refund_issued: bool = False


@router.patch("/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    payload: DisputeResolve,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from app.models.dispute import Dispute

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status == "resolved":
        raise HTTPException(status_code=400, detail="Dispute is already resolved")

    now = _now()
    dispute.status = "resolved"
    dispute.resolution_notes = payload.resolution_notes
    dispute.refund_issued = payload.refund_issued
    dispute.assigned_to = current_user.id
    dispute.resolved_at = now
    dispute.updated_at = now
    db.commit()

    _write_audit(
        db,
        admin_id=current_user.id,
        action="resolve_dispute",
        entity_type="dispute",
        entity_id=dispute_id,
        details={"resolution_notes": payload.resolution_notes},
    )
    db.commit()

    return {"dispute_id": dispute_id, "status": "resolved"}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@router.get("/analytics/overview")
def analytics_overview(current_user=Depends(_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func

    from app.models import Booking, Payment
    from app.models.dispute import Dispute

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_bookings = db.query(func.count(Booking.id)).scalar() or 0
    confirmed_b = (
        db.query(func.count(Booking.id)).filter(Booking.status == "confirmed").scalar()
        or 0
    )
    completed_b = (
        db.query(func.count(Booking.id)).filter(Booking.status == "completed").scalar()
        or 0
    )
    cancelled_b = (
        db.query(func.count(Booking.id)).filter(Booking.status == "cancelled").scalar()
        or 0
    )
    total_revenue = (
        db.query(func.sum(Payment.amount_usd))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    open_disputes = (
        db.query(func.count(Dispute.id)).filter(Dispute.status == "open").scalar() or 0
    )
    active_vehicles = (
        db.query(func.count(Vehicle.id)).filter(Vehicle.status == "verified").scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_b,
        "completed_bookings": completed_b,
        "cancelled_bookings": cancelled_b,
        "total_revenue_usd": float(total_revenue),
        "open_disputes": open_disputes,
        "active_vehicles": active_vehicles,
    }


@router.get("/analytics/bookings")
def analytics_bookings(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import Date, cast, func

    from app.models import Booking

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    rows = (
        db.query(
            cast(Booking.created_at, Date).label("day"),
            func.count(Booking.id).label("count"),
        )
        .filter(Booking.created_at >= cutoff)
        .group_by(cast(Booking.created_at, Date))
        .order_by(cast(Booking.created_at, Date))
        .all()
    )
    return [{"date": str(r.day), "count": r.count} for r in rows]


@router.get("/analytics/revenue")
def analytics_revenue(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import Date, cast, func

    from app.models import Payment

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    rows = (
        db.query(
            cast(Payment.created_at, Date).label("day"),
            func.sum(Payment.amount_usd).label("revenue"),
        )
        .filter(Payment.status == "completed", Payment.created_at >= cutoff)
        .group_by(cast(Payment.created_at, Date))
        .order_by(cast(Payment.created_at, Date))
        .all()
    )
    return [{"date": str(r.day), "revenue_usd": float(r.revenue or 0)} for r in rows]


@router.get("/analytics/fleet-utilisation")
def analytics_fleet(current_user=Depends(_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func

    from app.models import Booking

    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    verified_vehicles = (
        db.query(func.count(Vehicle.id)).filter(Vehicle.status == "verified").scalar()
        or 0
    )
    booked_vehicle_ids = [
        r[0]
        for r in db.query(Booking.vehicle_id)
        .filter(Booking.status.in_(["confirmed", "in_progress"]))
        .distinct()
        .all()
    ]
    return {
        "total_vehicles": total_vehicles,
        "verified_vehicles": verified_vehicles,
        "currently_booked": len(booked_vehicle_ids),
        "utilisation_pct": round(len(booked_vehicle_ids) / verified_vehicles * 100, 1)
        if verified_vehicles
        else 0,
    }


@router.get("/analytics/top-routes")
def analytics_top_routes(
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    from app.models import Booking

    rows = (
        db.query(
            Booking.pickup_location,
            Booking.dropoff_location,
            func.count(Booking.id).label("count"),
        )
        .group_by(Booking.pickup_location, Booking.dropoff_location)
        .order_by(func.count(Booking.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {"from": r.pickup_location, "to": r.dropoff_location, "count": r.count}
        for r in rows
    ]


@router.get("/analytics/conversion-funnel")
def analytics_funnel(current_user=Depends(_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func

    from app.models import Booking

    total = db.query(func.count(Booking.id)).scalar() or 0
    paid = (
        db.query(func.count(Booking.id))
        .filter(Booking.status != "pending_payment")
        .scalar()
        or 0
    )
    done = (
        db.query(func.count(Booking.id)).filter(Booking.status == "completed").scalar()
        or 0
    )
    return {
        "created": total,
        "payment_completed": paid,
        "trip_completed": done,
        "payment_rate_pct": round(paid / total * 100, 1) if total else 0,
        "completion_rate_pct": round(done / paid * 100, 1) if paid else 0,
    }


# ---------------------------------------------------------------------------
# Payments & Commissions
# ---------------------------------------------------------------------------


@router.get("/payments")
def list_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Payment)
    if status_filter:
        q = q.filter(Payment.status == status_filter)
    total = q.count()
    payments = (
        q.order_by(Payment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for p in payments:
        booking = db.query(Booking).filter(Booking.id == p.booking_id).first()
        customer = (
            db.query(User).filter(User.id == booking.customer_id).first()
            if booking
            else None
        )
        commission = (
            db.query(Commission).filter(Commission.booking_id == p.booking_id).first()
            if booking
            else None
        )
        result.append(
            {
                "id": p.id,
                "booking_id": p.booking_id,
                "booking_reference": booking.booking_reference if booking else None,
                "customer_name": customer.full_name if customer else None,
                "amount_usd": float(p.amount_usd) if p.amount_usd else None,
                "amount_ugx": float(p.amount_ugx) if p.amount_ugx else None,
                "currency": p.currency,
                "method": p.payment_method,
                "status": p.status,
                "platform_fee_usd": float(commission.platform_fee_usd)
                if commission and commission.platform_fee_usd
                else None,
                "owner_payout_ugx": float(commission.owner_payout_ugx)
                if commission and commission.owner_payout_ugx
                else None,
                "created_at": p.created_at,
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "payments": result}


@router.get("/payments/summary")
def payments_summary(current_user=Depends(_admin), db: Session = Depends(get_db)):
    from sqlalchemy import func

    total_collected = (
        db.query(func.sum(Payment.amount_usd))
        .filter(Payment.status == "completed")
        .scalar()
        or 0
    )
    total_pending = (
        db.query(func.count(Payment.id)).filter(Payment.status == "pending").scalar()
        or 0
    )
    total_failed = (
        db.query(func.count(Payment.id)).filter(Payment.status == "failed").scalar()
        or 0
    )
    total_completed = (
        db.query(func.count(Payment.id)).filter(Payment.status == "completed").scalar()
        or 0
    )
    platform_fees = db.query(func.sum(Commission.platform_fee_usd)).scalar() or 0
    owner_payouts = db.query(func.sum(Commission.owner_payout_ugx)).scalar() or 0
    return {
        "total_collected_usd": float(total_collected),
        "total_pending": int(total_pending),
        "total_failed": int(total_failed),
        "total_completed": int(total_completed),
        "platform_fees_usd": float(platform_fees),
        "owner_payouts_ugx": float(owner_payouts),
    }


# ---------------------------------------------------------------------------
# Vehicle Inspections (all statuses, for inspection queue)
# ---------------------------------------------------------------------------


@router.get("/inspections")
def list_inspections(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Vehicle)
    if status_filter:
        q = q.filter(Vehicle.status == status_filter)
    else:
        q = q.filter(Vehicle.status.in_(["pending", "pending_review"]))
    total = q.count()
    vehicles = (
        q.order_by(Vehicle.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for v in vehicles:
        owner = db.query(User).filter(User.id == v.owner_id).first()
        result.append(
            {
                "id": v.id,
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "registration_plate": v.registration_plate,
                "vehicle_type": v.vehicle_type,
                "status": v.status,
                "owner_name": owner.full_name if owner else None,
                "owner_email": owner.email if owner else None,
                "rejection_reason": v.rejection_reason,
                "created_at": v.created_at,
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "vehicles": result}


@router.get("/analytics/customer-segments")
def analytics_customer_segments(
    current_user=Depends(_admin), db: Session = Depends(get_db)
):
    from sqlalchemy import func

    from app.models import Booking

    total_customers = (
        db.query(func.count(User.id)).filter(User.role == "customer").scalar() or 0
    )
    booked_once = db.query(func.count(func.distinct(Booking.customer_id))).scalar() or 0
    repeat = (
        db.query(Booking.customer_id)
        .group_by(Booking.customer_id)
        .having(func.count(Booking.id) > 1)
        .count()
    )
    return {
        "total_customers": total_customers,
        "customers_who_booked": booked_once,
        "repeat_customers": repeat,
        "booking_rate_pct": round(booked_once / total_customers * 100, 1)
        if total_customers
        else 0,
        "repeat_rate_pct": round(repeat / booked_once * 100, 1) if booked_once else 0,
    }
