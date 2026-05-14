from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from .base import Base


class BookingPromotion(Base):
    __tablename__ = "booking_promotions"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    promotion_id = Column(String(36), ForeignKey("promotions.id"), nullable=False)
    discount_applied_ugx = Column(BIGINT, nullable=False)
    applied_at = Column(DateTime, nullable=False)


class BookingStop(Base):
    __tablename__ = "booking_stops"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    stop_order = Column(SmallInteger, nullable=False)
    location = Column(Text, nullable=False)
    lat = Column(Numeric)
    lng = Column(Numeric)
    estimated_arrival = Column(DateTime)
    notes = Column(Text)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_reference = Column(String, nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(String(36), ForeignKey("driver_profiles.id"), nullable=True)
    booking_type = Column(String, nullable=False)
    trip_type = Column(String, nullable=False)
    pickup_location = Column(Text, nullable=False)
    pickup_lat = Column(Numeric)
    pickup_lng = Column(Numeric)
    dropoff_location = Column(Text, nullable=False)
    dropoff_lat = Column(Numeric)
    dropoff_lng = Column(Numeric)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    actual_start_at = Column(DateTime)
    actual_end_at = Column(DateTime)
    total_days = Column(SmallInteger)
    flight_number = Column(String)
    flight_arrival_time = Column(DateTime)
    passenger_count = Column(SmallInteger, nullable=False)
    special_requests = Column(Text)
    status = Column(String, nullable=False)
    cancellation_reason = Column(Text)
    cancelled_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    cancelled_at = Column(DateTime)
    assigned_by_admin = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
