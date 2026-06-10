from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text

from .base import Base


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    triggered_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    lat = Column(Numeric, nullable=False)
    lng = Column(Numeric, nullable=False)
    location_address = Column(Text)
    alert_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    triggered_at = Column(DateTime, nullable=False)
