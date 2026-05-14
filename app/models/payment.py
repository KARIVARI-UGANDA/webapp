from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, Numeric, String, Text
from .base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    payer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount_ugx = Column(BIGINT, nullable=False)
    amount_usd = Column(Numeric)
    currency = Column(String, nullable=False, default="UGX")
    payment_method = Column(String, nullable=False)
    payment_channel = Column(String)
    gateway_reference = Column(String, unique=True)
    phone_number = Column(String)
    status = Column(String, nullable=False)
    paid_at = Column(DateTime)
    receipt_url = Column(Text)
    invoice_url = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True, nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    booking_ids = Column(Text)
    total_amount_ugx = Column(BIGINT, nullable=False)
    payout_method = Column(String, nullable=False)
    phone_number = Column(String)
    bank_account_number = Column(String)
    bank_name = Column(String)
    gateway_reference = Column(String, unique=True)
    status = Column(String, nullable=False)
    requested_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime)
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
