from sqlalchemy import JSON, Column, DateTime, ForeignKey, String

from .base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    actor_role = Column(String)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String(36), nullable=False)
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String)
    occurred_at = Column(DateTime, nullable=False)
