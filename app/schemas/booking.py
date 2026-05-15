from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class BookingCreate(BaseModel):
    booking_reference: str
    customer_id: str
    vehicle_id: str
    driver_id: Optional[str] = None
    booking_type: str
    trip_type: str
    pickup_location: str
    pickup_lat: Optional[Decimal] = None
    pickup_lng: Optional[Decimal] = None
    dropoff_location: str
    dropoff_lat: Optional[Decimal] = None
    dropoff_lng: Optional[Decimal] = None
    start_datetime: datetime
    end_datetime: datetime
    passenger_count: int
    flight_number: Optional[str] = None
    flight_arrival_time: Optional[datetime] = None
    special_requests: Optional[str] = None
    status: str
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    assigned_by_admin: Optional[str] = None


class BookingRead(BookingCreate):
    id: str
    total_days: Optional[int] = None
    actual_start_at: Optional[datetime] = None
    actual_end_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingPromotionRead(BaseModel):
    id: str
    booking_id: str
    promotion_id: str
    discount_applied_ugx: int
    applied_at: datetime

    class Config:
        from_attributes = True


class BookingStopRead(BaseModel):
    id: str
    booking_id: str
    stop_order: int
    location: str
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    estimated_arrival: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
