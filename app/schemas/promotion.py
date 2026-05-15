from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PromotionCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    minimum_booking_ugx: Optional[int] = None
    max_uses: Optional[int] = None
    uses_per_user: Optional[int] = None
    applicable_to: Optional[str] = None
    valid_from: datetime
    valid_to: datetime
    is_active: bool = True
    created_by: Optional[str] = None


class PromotionRead(PromotionCreate):
    id: str
    times_used: int
    created_at: datetime

    class Config:
        from_attributes = True
