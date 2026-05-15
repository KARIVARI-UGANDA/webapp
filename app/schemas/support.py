from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupportMessageCreate(BaseModel):
    ticket_id: str
    sender_id: str
    message_text: str
    attachment_url: Optional[str] = None
    is_internal_note: bool = False
    sent_at: datetime


class SupportMessageRead(SupportMessageCreate):
    id: str

    class Config:
        from_attributes = True


class SupportTicketCreate(BaseModel):
    user_id: str
    category: str
    subject: str
    description: str
    related_booking_id: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class SupportTicketRead(SupportTicketCreate):
    id: str

    class Config:
        from_attributes = True
