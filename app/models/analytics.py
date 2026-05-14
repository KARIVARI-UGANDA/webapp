from sqlalchemy import BIGINT, Column, Date, DateTime, Integer, String
from .base import Base


class AnalyticsDailySnapshot(Base):
    __tablename__ = "analytics_daily_snapshots"

    id = Column(String(36), primary_key=True, nullable=False)
    snapshot_date = Column(Date, nullable=False, unique=True)
    total_bookings = Column(Integer, nullable=False, default=0)
    completed_bookings = Column(Integer, nullable=False, default=0)
    cancelled_bookings = Column(Integer, nullable=False, default=0)
    new_customers = Column(Integer, nullable=False, default=0)
    new_vehicles = Column(Integer, nullable=False, default=0)
    gross_revenue_ugx = Column(BIGINT, nullable=False, default=0)
    commission_ugx = Column(BIGINT, nullable=False, default=0)
    payouts_ugx = Column(BIGINT, nullable=False, default=0)
    refunds_ugx = Column(BIGINT, nullable=False, default=0)
    open_disputes = Column(Integer, nullable=False, default=0)
    active_vehicles = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False)
