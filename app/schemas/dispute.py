from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DisputeEvidenceCreate(BaseModel):
    dispute_id: str
    submitted_by: str
    evidence_type: str
    file_url: str
    description: Optional[str] = None
    submitted_at: datetime


class DisputeEvidenceRead(DisputeEvidenceCreate):
    id: str

    class Config:
        from_attributes = True


class DisputeCreate(BaseModel):
    booking_id: str
    raised_by: str
    dispute_type: str
    description: str
    status: str
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    refund_issued: bool = False
    refund_id: Optional[str] = None
    opened_at: datetime


class DisputeRead(DisputeCreate):
    id: str
    resolved_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True
