from sqlalchemy import BIGINT, BOOLEAN, Column, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from .base import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(String(36), primary_key=True, nullable=False)
    code = Column(String, nullable=False, unique=True)
    description = Column(Text)
    discount_type = Column(String, nullable=False)
    discount_value = Column(Numeric, nullable=False)
    minimum_booking_ugx = Column(BIGINT)
    max_uses = Column(Integer)
    uses_per_user = Column(SmallInteger)
    times_used = Column(Integer, nullable=False, default=0)
    applicable_to = Column(String)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    is_active = Column(BOOLEAN, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
