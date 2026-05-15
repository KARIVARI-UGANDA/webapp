from datetime import date, datetime
from pydantic import BaseModel


class AnalyticsDailySnapshotCreate(BaseModel):
    snapshot_date: date
    total_bookings: int = 0
    completed_bookings: int = 0
    cancelled_bookings: int = 0
    new_customers: int = 0
    new_vehicles: int = 0
    gross_revenue_ugx: int = 0
    commission_ugx: int = 0
    payouts_ugx: int = 0
    refunds_ugx: int = 0
    open_disputes: int = 0
    active_vehicles: int = 0
    created_at: datetime


class AnalyticsDailySnapshotRead(AnalyticsDailySnapshotCreate):
    id: str

    class Config:
        from_attributes = True
