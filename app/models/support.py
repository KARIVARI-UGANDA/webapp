from sqlalchemy import BOOLEAN, Column, DateTime, ForeignKey, String, Text

from .base import Base


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(String(36), primary_key=True, nullable=False)
    ticket_id = Column(String(36), ForeignKey("support_tickets.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    attachment_url = Column(Text)
    is_internal_note = Column(BOOLEAN, nullable=False, default=False)
    sent_at = Column(DateTime, nullable=False)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    related_booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolution = Column(Text)
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
