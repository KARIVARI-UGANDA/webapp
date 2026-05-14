from sqlalchemy import BIGINT, BOOLEAN, Column, Date, DateTime, ForeignKey, Numeric, String
from .base import Base


class CommissionRule(Base):
    __tablename__ = "commission_rules"

    id = Column(String(36), primary_key=True, nullable=False)
    rule_name = Column(String, nullable=False)
    vehicle_type = Column(String)
    booking_type = Column(String)
    commission_rate = Column(Numeric, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    is_active = Column(BOOLEAN, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)


class Commission(Base):
    __tablename__ = "commissions"

    id = Column(String(36), primary_key=True, nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.id"), nullable=False)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    gross_amount_ugx = Column(BIGINT, nullable=False)
    commission_rate = Column(Numeric, nullable=False)
    commission_ugx = Column(BIGINT, nullable=False)
    owner_payout_ugx = Column(BIGINT, nullable=False)
    calculated_at = Column(DateTime, nullable=False)
