from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    ip_address: Optional[str] = None
    occurred_at: datetime


class AuditLogRead(AuditLogCreate):
    id: str

    class Config:
        from_attributes = True
