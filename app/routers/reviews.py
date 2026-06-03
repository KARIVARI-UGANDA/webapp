import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Booking, Review
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/reviews", tags=["reviews"])
_any_auth = get_current_user

REVIEWABLE_STATUSES = {"confirmed", "completed"}
VALID_TARGETS = {"vehicle", "trip"}


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReviewRequest(BaseModel):
    booking_id: str
    review_target: str          # "owner" | "vehicle" | "trip"
    overall_rating: int         # 1–5
    punctuality_rating: Optional[int] = None
    cleanliness_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    value_rating: Optional[int] = None
    review_text: Optional[str] = None

    @field_validator("overall_rating", "punctuality_rating", "cleanliness_rating",
                     "communication_rating", "value_rating", mode="before")
    @classmethod
    def rating_range(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("review_target")
    @classmethod
    def valid_target(cls, v):
        if v not in VALID_TARGETS:
            raise ValueError(f"review_target must be one of {VALID_TARGETS}")
        return v


class ReviewOut(BaseModel):
    id: str
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    review_target: str
    overall_rating: int
    punctuality_rating: Optional[int] = None
    cleanliness_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    value_rating: Optional[int] = None
    review_text: Optional[str] = None
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── POST /api/reviews/ ─────────────────────────────────────────────────────────
@router.post("/", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewRequest,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(
        Booking.id == payload.booking_id,
        Booking.customer_id == current_user.id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in REVIEWABLE_STATUSES:
        raise HTTPException(status_code=400, detail="You can only review confirmed or completed bookings")

    # Prevent duplicate reviews for the same booking + target
    existing = db.query(Review).filter(
        Review.booking_id == payload.booking_id,
        Review.reviewer_id == current_user.id,
        Review.review_target == payload.review_target,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"You have already reviewed the {payload.review_target} for this booking")

    # Determine who is being reviewed
    vehicle = db.query(Vehicle).filter(Vehicle.id == booking.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    reviewee_id = vehicle.owner_id

    review = Review(
        id=str(uuid.uuid4()),
        booking_id=payload.booking_id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        review_target=payload.review_target,
        overall_rating=payload.overall_rating,
        punctuality_rating=payload.punctuality_rating,
        cleanliness_rating=payload.cleanliness_rating,
        communication_rating=payload.communication_rating,
        value_rating=payload.value_rating,
        review_text=payload.review_text,
        is_public=True,
        is_flagged=False,
        created_at=_now(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ── GET /api/reviews/me ────────────────────────────────────────────────────────
@router.get("/me", response_model=List[ReviewOut])
def my_reviews(
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    return db.query(Review).filter(
        Review.reviewer_id == current_user.id,
    ).order_by(Review.created_at.desc()).all()


# ── GET /api/reviews/booking/{booking_id} ─────────────────────────────────────
@router.get("/booking/{booking_id}", response_model=List[ReviewOut])
def reviews_for_booking(
    booking_id: str,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    """Returns all reviews the current user wrote for a specific booking."""
    return db.query(Review).filter(
        Review.booking_id == booking_id,
        Review.reviewer_id == current_user.id,
    ).all()


# ── GET /api/reviews/ ─────────────────────────────────────────────────────────
@router.get("/", response_model=List[ReviewOut])
def list_reviews(
    reviewee_id: Optional[str] = None,
    review_target: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Review).filter(Review.is_public == True, Review.is_flagged == False)
    if reviewee_id:
        q = q.filter(Review.reviewee_id == reviewee_id)
    if review_target:
        q = q.filter(Review.review_target == review_target)
    return q.order_by(Review.created_at.desc()).limit(100).all()


# ── PATCH /api/reviews/{review_id}/flag ────────────────────────────────────────
@router.patch("/{review_id}/flag")
def flag_review(
    review_id: str,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_flagged = True
    db.commit()
    return {"message": "Review flagged for moderation"}
