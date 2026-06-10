from sqlalchemy import BOOLEAN, Column, DateTime, ForeignKey, String, Text

from .base import Base


class Message(Base):
    """Booking-scoped chat between customer and car owner (and admin)."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False
    )
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(BOOLEAN, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
