from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


ALLOWED_VEHICLE_TYPES = {"safari", "suv", "luxury", "minibus", "sedan", "other"}
ALLOWED_STATUSES = {"pending", "verified", "rejected", "suspended"}
ALLOWED_TRANSMISSIONS = {"manual", "automatic"}
ALLOWED_FUEL_TYPES = {"petrol", "diesel", "hybrid", "electric"}


class VehicleSubmit(BaseModel):
    """Payload an owner sends when submitting a new vehicle."""
    make: str
    model: str
    year: int
    color: str
    registration_plate: str
    vehicle_type: str
    transmission: str
    fuel_type: str
    passenger_capacity: int
    has_ac: bool = False
    has_wifi: bool = False
    has_child_seat: bool = False
    has_roof_rack: bool = False
    is_4wd: bool = False
    description: Optional[str] = None
    base_daily_rate_ugx: int          # primary rate in UGX
    rate_with_driver_ugx: Optional[int] = None
    service_area: Optional[str] = None  # e.g. "Kampala, Entebbe"

    @field_validator("vehicle_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v.lower() not in ALLOWED_VEHICLE_TYPES:
            raise ValueError(f"vehicle_type must be one of {ALLOWED_VEHICLE_TYPES}")
        return v.lower()

    @field_validator("year")
    @classmethod
    def valid_year(cls, v: int) -> int:
        if v < 1990 or v > 2030:
            raise ValueError("year must be between 1990 and 2030")
        return v

    @field_validator("passenger_capacity")
    @classmethod
    def valid_capacity(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("passenger_capacity must be between 1 and 50")
        return v

    @field_validator("base_daily_rate_ugx")
    @classmethod
    def valid_rate(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("base_daily_rate_ugx must be positive")
        return v


class VehicleUpdate(BaseModel):
    """Fields an owner can patch on a pending vehicle."""
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    vehicle_type: Optional[str] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    passenger_capacity: Optional[int] = None
    has_ac: Optional[bool] = None
    has_wifi: Optional[bool] = None
    has_child_seat: Optional[bool] = None
    has_roof_rack: Optional[bool] = None
    is_4wd: Optional[bool] = None
    description: Optional[str] = None
    base_daily_rate_ugx: Optional[int] = None
    rate_with_driver_ugx: Optional[int] = None
    service_area: Optional[str] = None


class VehiclePhotoRead(BaseModel):
    id: str
    vehicle_id: str
    photo_url: str
    photo_type: str
    is_primary: bool
    sort_order: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class VehicleRead(BaseModel):
    id: str
    owner_id: str
    make: str
    model: str
    year: int
    color: str
    registration_plate: str
    vehicle_type: str
    transmission: str
    fuel_type: str
    passenger_capacity: int
    has_ac: bool
    has_wifi: bool
    has_child_seat: bool
    has_roof_rack: bool
    is_4wd: bool
    description: Optional[str] = None
    base_daily_rate_ugx: int
    rate_with_driver_ugx: Optional[int] = None
    status: str
    rejection_reason: Optional[str] = None
    service_area: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleWithPhotos(VehicleRead):
    photos: List[VehiclePhotoRead] = []


# ---------- Admin ----------

class VerificationDecision(BaseModel):
    reason: Optional[str] = None  # required on reject, optional on approve


class VehicleAvailabilityRead(BaseModel):
    id: str
    vehicle_id: str
    available_from: date
    available_to: date
    availability_type: str
    block_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleDocumentRead(BaseModel):
    id: str
    vehicle_id: str
    document_type: str
    document_url: str
    document_number: Optional[str] = None
    issued_by: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: date
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class VehicleInspectionRead(BaseModel):
    id: str
    vehicle_id: str
    inspector_id: Optional[str] = None
    inspection_type: str
    scheduled_date: date
    conducted_date: Optional[date] = None
    overall_result: Optional[str] = None
    brakes_ok: Optional[bool] = None
    engine_ok: Optional[bool] = None
    tyres_ok: Optional[bool] = None
    seatbelts_ok: Optional[bool] = None
    lights_ok: Optional[bool] = None
    interior_clean: Optional[bool] = None
    ac_ok: Optional[bool] = None
    notes: Optional[str] = None
    required_repairs: Optional[str] = None
    report_url: Optional[str] = None
    next_inspection_due: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True
