from sqlalchemy import BOOLEAN, Column, DateTime, ForeignKey, String, Text
from .base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    notification_type = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    related_entity_type = Column(String)
    related_entity_id = Column(String(36))
    is_read = Column(BOOLEAN, nullable=False, default=False)
    read_at = Column(DateTime)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
