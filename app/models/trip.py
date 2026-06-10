from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String

from .base import Base


class TripLocationLog(Base):
    __tablename__ = "trip_location_logs"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    lat = Column(Numeric, nullable=False)
    lng = Column(Numeric, nullable=False)
    speed_kmh = Column(Numeric)
    heading = Column(Numeric)
    recorded_at = Column(DateTime, nullable=False)
