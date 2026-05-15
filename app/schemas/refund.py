from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RefundCreate(BaseModel):
    payment_id: str
    booking_id: str
    requested_by: str
    refund_amount_ugx: int
    refund_type: str
    reason: str
    status: str
    approved_by: Optional[str] = None
    gateway_reference: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None


class RefundRead(RefundCreate):
    id: str

    class Config:
        from_attributes = True
