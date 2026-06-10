from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String, Text

from .base import Base


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, nullable=False)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    refund_amount_ugx = Column(BIGINT, nullable=False)
    refund_type = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    gateway_reference = Column(String)
    requested_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
