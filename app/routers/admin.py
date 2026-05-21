import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import AuditLog, User, Vehicle
from app.models.driver import DriverProfile
from app.models.training import TrainingModule
from app.schemas.driver import AdminDriverDecision, DriverProfileRead, TrainingModuleCreate, TrainingModuleRead
from app.schemas.vehicle import VerificationDecision, VehicleRead
from app.services.notifications import create_notification

router = APIRouter(prefix="/admin", tags=["admin"])

_admin = require_role("admin")


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
    import json
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
    active_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "verified").scalar() or 0
    pending_verifications = db.query(func.count(Vehicle.id)).filter(Vehicle.status == "pending_review").scalar() or 0
    open_disputes = db.query(func.count(Dispute.id)).filter(Dispute.status == "open").scalar() or 0

    return {
        "total_users": total_users,
        "active_vehicles": active_vehicles,
        "pending_verifications": pending_verifications,
        "open_disputes": open_disputes,
    }


@router.get("/verifications/pending")
def list_pending_verifications(
    type: Optional[str] = Query("vehicle", regex="^(vehicle|owner|driver)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    if type == "vehicle":
        return db.query(Vehicle).filter(Vehicle.status == "pending").offset(offset).limit(page_size).all()

    if type == "driver":
        profiles = (
            db.query(DriverProfile)
            .filter(DriverProfile.verification_status == "pending")
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return [DriverProfileRead.model_validate(p) for p in profiles]

    # owner stub — Phase TBD
    raise HTTPException(status_code=501, detail="Pending owner verifications not yet implemented")


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
        raise HTTPException(status_code=400, detail=f"Vehicle is '{v.status}', not pending")

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
        raise HTTPException(status_code=422, detail="A reason is required when rejecting a vehicle")

    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if v.status not in ("pending", "verified"):
        raise HTTPException(status_code=400, detail=f"Cannot reject a vehicle with status '{v.status}'")

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
# Verifications — Drivers
# ---------------------------------------------------------------------------

@router.patch("/drivers/{driver_profile_id}/approve", response_model=DriverProfileRead)
def approve_driver(
    driver_profile_id: str,
    payload: AdminDriverDecision = AdminDriverDecision(),
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    profile = db.query(DriverProfile).filter(DriverProfile.id == driver_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    if profile.verification_status != "pending":
        raise HTTPException(status_code=400, detail=f"Driver status is '{profile.verification_status}', not pending")

    profile.verification_status = "verified"
    profile.updated_at = _now()
    db.add(profile)

    _write_audit(db, admin_id=current_user.id, action="verify_driver",
                 entity_type="driver_profile", entity_id=driver_profile_id)

    create_notification(db, user_id=profile.user_id,
                        notification_type="verification_approved",
                        title="Driver verification approved!",
                        body="You are now verified on Karivari and can be assigned to trips.",
                        related_entity_type="driver_profile", related_entity_id=driver_profile_id)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/drivers/{driver_profile_id}/reject", response_model=DriverProfileRead)
def reject_driver(
    driver_profile_id: str,
    payload: AdminDriverDecision,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    if not payload.reason:
        raise HTTPException(status_code=422, detail="A reason is required when rejecting a driver")

    profile = db.query(DriverProfile).filter(DriverProfile.id == driver_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    profile.verification_status = "rejected"
    profile.updated_at = _now()
    db.add(profile)

    _write_audit(db, admin_id=current_user.id, action="reject_driver",
                 entity_type="driver_profile", entity_id=driver_profile_id,
                 details={"reason": payload.reason})

    create_notification(db, user_id=profile.user_id,
                        notification_type="verification_rejected",
                        title="Driver verification unsuccessful",
                        body=f"Your application was not approved. Reason: {payload.reason}",
                        related_entity_type="driver_profile", related_entity_id=driver_profile_id)
    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Training Modules (admin manages the catalogue)
# ---------------------------------------------------------------------------

@router.get("/training-modules", response_model=List[TrainingModuleRead])
def list_training_modules(current_user=Depends(_admin), db: Session = Depends(get_db)):
    return db.query(TrainingModule).order_by(TrainingModule.order_index).all()


@router.post("/training-modules", response_model=TrainingModuleRead, status_code=status.HTTP_201_CREATED)
def create_training_module(
    payload: TrainingModuleCreate,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    module = TrainingModule(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        content_url=payload.content_url,
        order_index=payload.order_index,
        is_active=payload.is_active,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@router.patch("/training-modules/{module_id}", response_model=TrainingModuleRead)
def update_training_module(
    module_id: str,
    payload: TrainingModuleCreate,
    current_user=Depends(_admin),
    db: Session = Depends(get_db),
):
    module = db.query(TrainingModule).filter(TrainingModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(module, field, value)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


# ---------------------------------------------------------------------------
# Tourist KYC (Phase 7)
# ---------------------------------------------------------------------------

@router.get("/kyc/manual-review")
def list_kyc_manual_review(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


@router.patch("/kyc/{user_id}/approve")
def approve_kyc(user_id: str, current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


@router.patch("/kyc/{user_id}/reject")
def reject_kyc(user_id: str, current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


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
def list_all_bookings(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 13")


@router.patch("/bookings/{booking_id}/override-status")
def override_booking_status(booking_id: str, current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 13")


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------

@router.get("/disputes")
def list_disputes(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 13")


@router.patch("/disputes/{dispute_id}/resolve")
def resolve_dispute(dispute_id: str, current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 13")


# ---------------------------------------------------------------------------
# Analytics (Phase 14)
# ---------------------------------------------------------------------------

@router.get("/analytics/overview")
def analytics_overview(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/bookings")
def analytics_bookings(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/revenue")
def analytics_revenue(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/fleet-utilisation")
def analytics_fleet(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/top-routes")
def analytics_top_routes(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/conversion-funnel")
def analytics_funnel(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/driver-performance")
def analytics_driver_performance(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")


@router.get("/analytics/customer-segments")
def analytics_customer_segments(current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 14")
