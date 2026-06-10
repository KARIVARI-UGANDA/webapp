from sqlalchemy import BOOLEAN, Column, DateTime, ForeignKey, SmallInteger, String, Text

from .base import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    review_target = Column(String, nullable=False)
    overall_rating = Column(SmallInteger, nullable=False)
    punctuality_rating = Column(SmallInteger)
    cleanliness_rating = Column(SmallInteger)
    communication_rating = Column(SmallInteger)
    value_rating = Column(SmallInteger)
    review_text = Column(Text)
    is_public = Column(BOOLEAN, nullable=False, default=True)
    is_flagged = Column(BOOLEAN, nullable=False, default=False)
    flagged_reason = Column(Text)
    owner_response = Column(Text)
    owner_responded_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
