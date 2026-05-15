from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EmergencyAlertCreate(BaseModel):
    booking_id: str
    triggered_by: str
    lat: Decimal
    lng: Decimal
    location_address: Optional[str] = None
    alert_type: str
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    triggered_at: datetime


class EmergencyAlertRead(EmergencyAlertCreate):
    id: str

    class Config:
        from_attributes = True
