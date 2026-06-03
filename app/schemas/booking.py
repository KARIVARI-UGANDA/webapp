from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class BookingRequest(BaseModel):
    """Simplified payload sent by the booking widget. All trips are with the car owner as driver."""
    vehicle_id: str
    pickup_date: str           # YYYY-MM-DD
    return_date: str           # YYYY-MM-DD
    pickup_location: str
    dropoff_location: str
    passenger_count: int = 1
    special_requests: Optional[str] = None


class BookingPaymentResponse(BaseModel):
    booking_id: str
    booking_reference: str
    client_secret: str         # Stripe PaymentIntent client_secret
    amount_usd: float


class BookingCreate(BaseModel):
    booking_reference: str
    customer_id: str
    vehicle_id: str
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


class VehicleSnapshot(BaseModel):
    id: str
    make: str
    model: str
    year: int
    vehicle_type: str
    base_daily_rate_ugx: int
    primary_photo_url: Optional[str] = None


class BookingListItem(BaseModel):
    id: str
    booking_reference: str
    vehicle_id: str
    booking_type: str
    pickup_location: str
    dropoff_location: str
    start_datetime: datetime
    end_datetime: datetime
    total_days: Optional[int] = None
    passenger_count: int
    status: str
    created_at: datetime
    amount_ugx: Optional[int] = None
    amount_usd: Optional[float] = None
    vehicle: Optional[VehicleSnapshot] = None


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
