from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: str
    notification_type: str
    channel: str
    title: str
    body: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class NotificationRead(NotificationCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
