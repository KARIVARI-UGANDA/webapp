from sqlalchemy import BOOLEAN, Column, Date, DateTime, ForeignKey, String, Text
from .base import Base


class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"

    id = Column(String(36), primary_key=True, nullable=False)
    dispute_id = Column(String(36), ForeignKey("disputes.id"), nullable=False)
    submitted_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    evidence_type = Column(String, nullable=False)
    file_url = Column(Text, nullable=False)
    description = Column(Text)
    submitted_at = Column(DateTime, nullable=False)


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    raised_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    dispute_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text)
    refund_issued = Column(BOOLEAN, nullable=False, default=False)
    refund_id = Column(String(36), ForeignKey("refunds.id"), nullable=True)
    opened_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False)
