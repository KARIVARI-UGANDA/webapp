from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator


ALLOWED_STATUSES = {"pending", "verified", "rejected", "suspended"}


class DriverProfileCreate(BaseModel):
    """Driver fills this in during onboarding."""
    license_number: str
    license_class: str
    license_expiry: date
    license_doc_url: str
    years_experience: Optional[int] = None
    languages_spoken: Optional[str] = None   # JSON: ["English","Swahili"]
    specialties: Optional[str] = None        # JSON: ["photography","wildlife"]
    bio: Optional[str] = None
    has_first_aid: bool = False
    first_aid_cert_url: Optional[str] = None
    police_clearance_url: Optional[str] = None
    police_clearance_exp: Optional[date] = None


class DriverProfileUpdate(BaseModel):
    license_class: Optional[str] = None
    license_expiry: Optional[date] = None
    license_doc_url: Optional[str] = None
    years_experience: Optional[int] = None
    languages_spoken: Optional[str] = None
    specialties: Optional[str] = None
    bio: Optional[str] = None
    has_first_aid: Optional[bool] = None
    first_aid_cert_url: Optional[str] = None
    police_clearance_url: Optional[str] = None
    police_clearance_exp: Optional[date] = None


class DriverProfileRead(BaseModel):
    id: str
    user_id: str
    license_number: str
    license_class: str
    license_expiry: date
    license_doc_url: str
    years_experience: Optional[int] = None
    languages_spoken: Optional[str] = None
    specialties: Optional[str] = None
    bio: Optional[str] = None
    has_first_aid: bool
    first_aid_cert_url: Optional[str] = None
    police_clearance_url: Optional[str] = None
    police_clearance_exp: Optional[date] = None
    verification_status: str
    total_trips: int
    average_rating: Optional[float] = None
    training_completed: bool
    training_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingModuleRead(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    order_index: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class TrainingModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_url: Optional[str] = None
    order_index: Optional[int] = None
    is_active: bool = True


class TrainingProgressRead(BaseModel):
    id: str
    driver_id: str
    module_id: str
    completed_at: Optional[datetime] = None
    score: Optional[int] = None

    class Config:
        from_attributes = True


class TrainingModuleWithStatus(TrainingModuleRead):
    """Module info + whether this driver has completed it."""
    completed: bool
    completed_at: Optional[datetime] = None
    score: Optional[int] = None


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


class AdminDriverDecision(BaseModel):
    reason: Optional[str] = None
