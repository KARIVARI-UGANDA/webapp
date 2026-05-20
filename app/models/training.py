from sqlalchemy import BOOLEAN, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from .base import Base


class TrainingModule(Base):
    __tablename__ = "training_modules"

    id = Column(String(36), primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    content_url = Column(Text)       # video / pdf path
    order_index = Column(Integer)
    is_active = Column(BOOLEAN, nullable=False, default=True)


class DriverTrainingProgress(Base):
    __tablename__ = "driver_training_progress"

    id = Column(String(36), primary_key=True, nullable=False)
    driver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    module_id = Column(String(36), ForeignKey("training_modules.id"), nullable=False)
    completed_at = Column(DateTime)
    score = Column(Integer)          # optional quiz score

    __table_args__ = (UniqueConstraint("driver_id", "module_id", name="uq_driver_module"),)
