from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class VehicleCreate(BaseModel):
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
    has_ac: bool = False
    has_wifi: bool = False
    has_child_seat: bool = False
    has_roof_rack: bool = False
    is_4wd: bool = False
    description: Optional[str] = None
    base_daily_rate_ugx: int
    rate_with_driver_ugx: Optional[int] = None
    hourly_rate_ugx: Optional[int] = None
    km_rate_ugx: Optional[int] = None
    status: str
    rejection_reason: Optional[str] = None
    service_area: Optional[str] = None


class VehicleRead(VehicleCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
