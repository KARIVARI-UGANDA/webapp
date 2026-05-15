from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    full_name: str
    email: str
    phone_number: str
    password: str
    role: str
    account_type: str
    profile_photo_url: Optional[str] = None
    preferred_language: Optional[str] = None
    corporate_id: Optional[str] = None
    two_fa_enabled: Optional[bool] = False
    two_fa_secret: Optional[str] = None


class UserRead(BaseModel):
    id: str
    full_name: str
    email: str
    phone_number: str
    role: str
    account_type: str
    profile_photo_url: Optional[str] = None
    preferred_language: Optional[str] = None
    corporate_id: Optional[str] = None
    is_verified: bool
    is_active: bool
    two_fa_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
