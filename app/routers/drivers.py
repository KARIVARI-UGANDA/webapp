import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Booking
from app.models.driver import DriverProfile
from app.models.training import DriverTrainingProgress, TrainingModule
from app.schemas.driver import (
    DriverProfileCreate,
    DriverProfileRead,
    DriverProfileUpdate,
    TrainingModuleWithStatus,
)

router = APIRouter(prefix="/drivers", tags=["drivers"])

_driver = require_role("driver")
_any_auth = get_current_user


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_profile_or_404(user_id: str, db: Session) -> DriverProfile:
    p = db.query(DriverProfile).filter(DriverProfile.user_id == user_id).first()
    if not p:
        raise HTTPException(
            status_code=404,
            detail="Driver profile not found. Submit your profile to begin onboarding.",
        )
    return p


def _check_training_completion(driver_id: str, profile: DriverProfile, db: Session):
    """Flip training_completed if all active modules are done."""
    total_active = db.query(TrainingModule).filter(TrainingModule.is_active == True).count()
    completed = (
        db.query(DriverTrainingProgress)
        .filter(
            DriverTrainingProgress.driver_id == driver_id,
            DriverTrainingProgress.completed_at.isnot(None),
        )
        .count()
    )
    if total_active > 0 and completed >= total_active and not profile.training_completed:
        profile.training_completed = True
        profile.training_completed_at = _now()
        profile.updated_at = _now()
        db.add(profile)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get("/me/profile", response_model=DriverProfileRead)
def get_driver_profile(
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    return _get_profile_or_404(current_user.id, db)


@router.post("/me/profile", response_model=DriverProfileRead, status_code=status.HTTP_201_CREATED)
def create_driver_profile(
    payload: DriverProfileCreate,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    existing = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Driver profile already exists. Use PATCH to update.")

    if db.query(DriverProfile).filter(DriverProfile.license_number == payload.license_number).first():
        raise HTTPException(status_code=400, detail="License number already registered.")

    now = _now()
    profile = DriverProfile(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        license_number=payload.license_number,
        license_class=payload.license_class,
        license_expiry=payload.license_expiry,
        license_doc_url=payload.license_doc_url,
        years_experience=payload.years_experience,
        languages_spoken=payload.languages_spoken,
        specialties=payload.specialties,
        bio=payload.bio,
        has_first_aid=payload.has_first_aid,
        first_aid_cert_url=payload.first_aid_cert_url,
        police_clearance_url=payload.police_clearance_url,
        police_clearance_exp=payload.police_clearance_exp,
        verification_status="pending",
        training_completed=False,
        total_trips=0,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/me/profile", response_model=DriverProfileRead)
def update_driver_profile(
    payload: DriverProfileUpdate,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    profile = _get_profile_or_404(current_user.id, db)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    profile.updated_at = _now()
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Trips
# ---------------------------------------------------------------------------

@router.get("/me/trips")
def get_driver_trips(
    trip_status: Optional[str] = Query(None, alias="status", regex="^(upcoming|active|past)$"),
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    from app.models.vehicle import Vehicle, VehiclePhoto
    from app.models.user import User

    profile = _get_profile_or_404(current_user.id, db)

    q = db.query(Booking).filter(Booking.driver_id == profile.id)

    if trip_status == "upcoming":
        q = q.filter(Booking.status == "confirmed")
    elif trip_status == "active":
        q = q.filter(Booking.status == "in_progress")
    elif trip_status == "past":
        q = q.filter(Booking.status.in_(["completed", "cancelled"]))

    trips = q.order_by(Booking.start_datetime.desc()).all()

    result = []
    for t in trips:
        vehicle = db.query(Vehicle).filter(Vehicle.id == t.vehicle_id).first()
        customer = db.query(User).filter(User.id == t.customer_id).first()
        photo = None
        if vehicle:
            photo = (
                db.query(VehiclePhoto)
                .filter(VehiclePhoto.vehicle_id == vehicle.id, VehiclePhoto.is_primary.is_(True))
                .first()
                or db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle.id).first()
            )
        result.append({
            "id": t.id,
            "booking_reference": t.booking_reference,
            "booking_type": t.booking_type,
            "status": t.status,
            "pickup_location": t.pickup_location,
            "dropoff_location": t.dropoff_location,
            "start_datetime": t.start_datetime.isoformat() if t.start_datetime else None,
            "end_datetime": t.end_datetime.isoformat() if t.end_datetime else None,
            "total_days": t.total_days,
            "passenger_count": t.passenger_count,
            "vehicle": {
                "make": vehicle.make if vehicle else None,
                "model": vehicle.model if vehicle else None,
                "year": vehicle.year if vehicle else None,
                "photo_url": photo.photo_url if photo else None,
            } if vehicle else None,
            "customer_name": customer.full_name if customer else None,
        })

    return {"total": len(result), "trips": result}


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

@router.get("/me/training", response_model=List[TrainingModuleWithStatus])
def get_training_modules(
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    modules = (
        db.query(TrainingModule)
        .filter(TrainingModule.is_active == True)
        .order_by(TrainingModule.order_index)
        .all()
    )

    progress_map = {
        p.module_id: p
        for p in db.query(DriverTrainingProgress)
        .filter(DriverTrainingProgress.driver_id == current_user.id)
        .all()
    }

    result = []
    for m in modules:
        prog = progress_map.get(m.id)
        result.append(
            TrainingModuleWithStatus(
                id=m.id,
                title=m.title,
                description=m.description,
                content_url=m.content_url,
                order_index=m.order_index,
                is_active=m.is_active,
                completed=prog is not None and prog.completed_at is not None,
                completed_at=prog.completed_at if prog else None,
                score=prog.score if prog else None,
            )
        )
    return result


@router.post("/me/training/{module_id}/complete")
def complete_training_module(
    module_id: str,
    score: Optional[int] = None,
    current_user=Depends(_driver),
    db: Session = Depends(get_db),
):
    module = db.query(TrainingModule).filter(
        TrainingModule.id == module_id,
        TrainingModule.is_active == True,
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="Training module not found or inactive")

    profile = _get_profile_or_404(current_user.id, db)

    existing = db.query(DriverTrainingProgress).filter(
        DriverTrainingProgress.driver_id == current_user.id,
        DriverTrainingProgress.module_id == module_id,
    ).first()

    now = _now()
    if existing:
        existing.completed_at = now
        if score is not None:
            existing.score = score
        db.add(existing)
    else:
        db.add(
            DriverTrainingProgress(
                id=str(uuid.uuid4()),
                driver_id=current_user.id,
                module_id=module_id,
                completed_at=now,
                score=score,
            )
        )

    db.flush()  # make the new progress row visible to the completion count query
    _check_training_completion(current_user.id, profile, db)
    db.commit()

    return {
        "module_id": module_id,
        "module_title": module.title,
        "completed_at": now,
        "training_fully_completed": profile.training_completed,
    }


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

@router.get("/{driver_id}/reviews")
def get_driver_reviews(driver_id: str):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 10")
