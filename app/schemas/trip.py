from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TripLocationLogCreate(BaseModel):
    booking_id: str
    driver_id: str
    lat: Decimal
    lng: Decimal
    speed_kmh: Optional[Decimal] = None
    heading: Optional[Decimal] = None
    recorded_at: datetime


class TripLocationLogRead(TripLocationLogCreate):
    id: str

    class Config:
        from_attributes = True
