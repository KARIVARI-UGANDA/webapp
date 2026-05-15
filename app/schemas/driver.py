from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DriverProfileCreate(BaseModel):
    user_id: str
    license_number: str
    license_class: str
    license_expiry: date
    license_doc_url: str
    years_experience: Optional[int] = None
    languages_spoken: Optional[str] = None
    specialties: Optional[str] = None
    bio: Optional[str] = None
    has_first_aid: bool = False
    first_aid_cert_url: Optional[str] = None
    police_clearance_url: Optional[str] = None
    police_clearance_exp: Optional[date] = None
    verification_status: str
    total_trips: int = 0
    average_rating: Optional[float] = None


class DriverProfileRead(DriverProfileCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DriverVehicleAssignmentCreate(BaseModel):
    driver_id: str
    vehicle_id: str
    is_primary: bool = False
    assigned_from: Optional[date] = None
    assigned_to: Optional[date] = None


class DriverVehicleAssignmentRead(DriverVehicleAssignmentCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
