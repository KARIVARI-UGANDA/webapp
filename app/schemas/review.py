from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReviewCreate(BaseModel):
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
    is_public: bool = True
    is_flagged: bool = False
    flagged_reason: Optional[str] = None
    owner_response: Optional[str] = None
    owner_responded_at: Optional[datetime] = None


class ReviewRead(ReviewCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
