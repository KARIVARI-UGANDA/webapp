from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CorporateAccountCreate(BaseModel):
    company_name: str
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    billing_email: str
    billing_phone: Optional[str] = None
    billing_address: Optional[str] = None
    monthly_limit_ugx: Optional[int] = None
    primary_contact_id: str
    is_active: bool = True


class CorporateAccountRead(CorporateAccountCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
