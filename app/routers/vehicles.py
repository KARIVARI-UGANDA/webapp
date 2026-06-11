import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import Vehicle, VehiclePhoto
from app.models.booking import Booking
from app.schemas.vehicle import (
    VehiclePhotoRead,
    VehicleRead,
    VehicleStatusUpdate,
    VehicleSubmit,
    VehicleUpdate,
    VehicleWithPhotos,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_owner_or_admin = require_role("owner", "admin")
_any_auth = get_current_user

MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PHOTOS_PER_VEHICLE = 8
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _get_own_vehicle(vehicle_id: str, current_user, db: Session) -> Vehicle:
    """Load a vehicle and enforce owner-or-admin access."""
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    if current_user.role != "admin" and v.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not own this vehicle")
    return v


# ---------------------------------------------------------------------------
# Browse
# ---------------------------------------------------------------------------


@router.get("/", response_model=List[VehicleWithPhotos])
def list_vehicles(
    location: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    min_seats: Optional[int] = Query(None, ge=1),
    max_daily_rate_ugx: Optional[int] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Public browse — pending and verified vehicles (excludes rejected/suspended and actively booked)."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    booked_ids = (
        db.query(Booking.vehicle_id)
        .filter(
            Booking.status == "confirmed",
            Booking.end_datetime >= now,
        )
        .subquery()
    )
    q = db.query(Vehicle).filter(
        Vehicle.status.in_(["pending", "verified"]),
        ~Vehicle.id.in_(booked_ids),
    )

    if location:
        q = q.filter(Vehicle.service_area.ilike(f"%{location}%"))
    if vehicle_type:
        q = q.filter(Vehicle.vehicle_type == vehicle_type.lower())
    if min_seats:
        q = q.filter(Vehicle.passenger_capacity >= min_seats)
    if max_daily_rate_ugx:
        q = q.filter(Vehicle.base_daily_rate_ugx <= max_daily_rate_ugx)

    offset = (page - 1) * page_size
    vehicles = q.offset(offset).limit(page_size).all()

    result = []
    for v in vehicles:
        photos = db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == v.id).all()
        vwp = VehicleWithPhotos.model_validate(v)
        vwp.photos = [VehiclePhotoRead.model_validate(p) for p in photos]
        result.append(vwp)
    return result


@router.get("/mine", response_model=List[VehicleWithPhotos])
def my_vehicles(
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Owner retrieves their own vehicles regardless of status."""
    vehicles = db.query(Vehicle).filter(Vehicle.owner_id == current_user.id).all()
    result = []
    for v in vehicles:
        photos = db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == v.id).all()
        vwp = VehicleWithPhotos.model_validate(v)
        vwp.photos = [VehiclePhotoRead.model_validate(p) for p in photos]
        result.append(vwp)
    return result


@router.get("/{vehicle_id}", response_model=VehicleWithPhotos)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    photos = db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle_id).all()
    result = VehicleWithPhotos.model_validate(v)
    result.photos = [VehiclePhotoRead.model_validate(p) for p in photos]
    return result


# ---------------------------------------------------------------------------
# Owner CRUD
# ---------------------------------------------------------------------------


@router.post("/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleSubmit,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    # Duplicate plate check
    if (
        db.query(Vehicle)
        .filter(Vehicle.registration_plate == payload.registration_plate)
        .first()
    ):
        raise HTTPException(
            status_code=400, detail="Registration plate already registered"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    owner_id = current_user.id if current_user.role == "owner" else current_user.id

    v = Vehicle(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        color=payload.color,
        registration_plate=payload.registration_plate,
        vehicle_type=payload.vehicle_type,
        transmission=payload.transmission,
        fuel_type=payload.fuel_type,
        passenger_capacity=payload.passenger_capacity,
        has_ac=payload.has_ac,
        has_wifi=payload.has_wifi,
        has_child_seat=payload.has_child_seat,
        has_roof_rack=payload.has_roof_rack,
        is_4wd=payload.is_4wd,
        description=payload.description,
        base_daily_rate_ugx=payload.base_daily_rate_ugx,
        service_area=payload.service_area,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    v = _get_own_vehicle(vehicle_id, current_user, db)

    if v.status == "verified" and current_user.role != "admin":
        raise HTTPException(
            status_code=400,
            detail="Verified vehicles cannot be edited. Contact support.",
        )

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(v, field, value)
    v.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.patch("/{vehicle_id}/availability", response_model=VehicleRead)
def set_vehicle_availability(
    vehicle_id: str,
    payload: VehicleStatusUpdate,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    v = _get_own_vehicle(vehicle_id, current_user, db)

    if current_user.role != "admin":
        if payload.status not in {"verified", "suspended"}:
            raise HTTPException(
                status_code=403,
                detail="Owners may only pause (suspend) or resume (verified) their vehicles.",
            )
        if v.status not in {"verified", "suspended"}:
            raise HTTPException(
                status_code=400,
                detail="Only verified or suspended vehicles can be paused or resumed.",
            )

    v.status = payload.status
    v.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: str,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    v = _get_own_vehicle(vehicle_id, current_user, db)
    if v.status == "verified":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a verified vehicle. Suspend it first.",
        )
    db.delete(v)
    db.commit()


# ---------------------------------------------------------------------------
# Photo upload
# ---------------------------------------------------------------------------


@router.post("/{vehicle_id}/photos", response_model=List[VehiclePhotoRead])
async def upload_photos(
    vehicle_id: str,
    files: List[UploadFile] = File(...),
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    _get_own_vehicle(vehicle_id, current_user, db)

    existing_count = (
        db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle_id).count()
    )
    if existing_count + len(files) > MAX_PHOTOS_PER_VEHICLE:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_PHOTOS_PER_VEHICLE} photos allowed. Vehicle already has {existing_count}.",
        )

    saved: list[VehiclePhoto] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for f in files:
        content_type = f.content_type or ""
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File '{f.filename}' has unsupported type '{content_type}'. Allowed: jpeg, png, webp",
            )

        data = await f.read()
        if len(data) > MAX_PHOTO_SIZE_BYTES:
            raise HTTPException(
                status_code=400, detail=f"File '{f.filename}' exceeds 10 MB limit"
            )

        photo_id = str(uuid.uuid4())
        is_primary = existing_count == 0 and len(saved) == 0
        photo = VehiclePhoto(
            id=photo_id,
            vehicle_id=vehicle_id,
            photo_url=f"/api/vehicles/{vehicle_id}/photos/{photo_id}/image",
            photo_data=data,
            content_type=content_type,
            photo_type="exterior",
            is_primary=is_primary,
            sort_order=existing_count + len(saved),
            uploaded_at=now,
        )
        db.add(photo)
        saved.append(photo)

    db.commit()
    for p in saved:
        db.refresh(p)
    return [VehiclePhotoRead.model_validate(p) for p in saved]


# ---------------------------------------------------------------------------
# Photo management
# ---------------------------------------------------------------------------


@router.get("/{vehicle_id}/photos/{photo_id}/image")
def serve_photo(
    vehicle_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
):
    """Serve a vehicle photo directly from the database."""
    photo = (
        db.query(VehiclePhoto)
        .filter(
            VehiclePhoto.id == photo_id,
            VehiclePhoto.vehicle_id == vehicle_id,
        )
        .first()
    )
    if not photo or not photo.photo_data:
        raise HTTPException(status_code=404, detail="Photo not found")
    return Response(
        content=photo.photo_data,
        media_type=photo.content_type or "image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.delete(
    "/{vehicle_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_photo(
    vehicle_id: str,
    photo_id: str,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    _get_own_vehicle(vehicle_id, current_user, db)
    photo = (
        db.query(VehiclePhoto)
        .filter(
            VehiclePhoto.id == photo_id,
            VehiclePhoto.vehicle_id == vehicle_id,
        )
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    db.delete(photo)
    db.commit()

    remaining = (
        db.query(VehiclePhoto)
        .filter(VehiclePhoto.vehicle_id == vehicle_id)
        .order_by(VehiclePhoto.sort_order)
        .first()
    )
    if remaining and not remaining.is_primary:
        remaining.is_primary = True
        db.commit()


@router.patch(
    "/{vehicle_id}/photos/{photo_id}/primary", response_model=VehiclePhotoRead
)
def set_primary_photo(
    vehicle_id: str,
    photo_id: str,
    current_user=Depends(_owner_or_admin),
    db: Session = Depends(get_db),
):
    _get_own_vehicle(vehicle_id, current_user, db)
    db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == vehicle_id).update(
        {"is_primary": False}
    )
    photo = (
        db.query(VehiclePhoto)
        .filter(
            VehiclePhoto.id == photo_id,
            VehiclePhoto.vehicle_id == vehicle_id,
        )
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    photo.is_primary = True
    db.commit()
    db.refresh(photo)
    return VehiclePhotoRead.model_validate(photo)


# ---------------------------------------------------------------------------
# Availability check (stub — full overlap logic in Phase 6)
# ---------------------------------------------------------------------------


@router.get("/{vehicle_id}/availability")
def get_availability(
    vehicle_id: str,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    db: Session = Depends(get_db),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    # Full overlap query implemented in Phase 6
    return {
        "vehicle_id": vehicle_id,
        "available": True,
        "note": "Full availability logic in Phase 6",
    }


@router.get("/{vehicle_id}/reviews")
def get_vehicle_reviews(vehicle_id: str, db: Session = Depends(get_db)):
    from app.models import Booking
    from app.models.review import Review
    from app.models.user import User

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    booking_ids = [
        b.id for b in db.query(Booking).filter(Booking.vehicle_id == vehicle_id).all()
    ]
    if not booking_ids:
        return []

    reviews = (
        db.query(Review)
        .filter(
            Review.booking_id.in_(booking_ids),
            Review.review_target.in_(["vehicle", "trip"]),
            Review.is_public,
            ~Review.is_flagged,
        )
        .order_by(Review.created_at.desc())
        .limit(50)
        .all()
    )

    result = []
    for r in reviews:
        reviewer = db.query(User).filter(User.id == r.reviewer_id).first()
        result.append(
            {
                "id": r.id,
                "reviewer_name": reviewer.full_name if reviewer else "Anonymous",
                "review_target": r.review_target,
                "overall_rating": r.overall_rating,
                "cleanliness_rating": r.cleanliness_rating,
                "communication_rating": r.communication_rating,
                "value_rating": r.value_rating,
                "review_text": r.review_text,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return result
