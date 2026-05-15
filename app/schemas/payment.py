from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    booking_id: str
    payer_id: str
    amount_ugx: int
    amount_usd: Optional[Decimal] = None
    currency: str = "UGX"
    payment_method: str
    payment_channel: Optional[str] = None
    gateway_reference: Optional[str] = None
    phone_number: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    receipt_url: Optional[str] = None
    invoice_url: Optional[str] = None


class PaymentRead(PaymentCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayoutCreate(BaseModel):
    owner_id: str
    booking_ids: Optional[str] = None
    total_amount_ugx: int
    payout_method: str
    phone_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    gateway_reference: Optional[str] = None
    status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None


class PayoutRead(PayoutCreate):
    id: str

    class Config:
        from_attributes = True
