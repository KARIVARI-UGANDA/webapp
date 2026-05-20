from sqlalchemy import BOOLEAN, Column, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from .base import Base


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    license_number = Column(String, nullable=False, unique=True)
    license_class = Column(String, nullable=False)
    license_expiry = Column(Date, nullable=False)
    license_doc_url = Column(Text, nullable=False)
    years_experience = Column(SmallInteger)
    languages_spoken = Column(Text)
    specialties = Column(Text)
    bio = Column(Text)
    has_first_aid = Column(BOOLEAN, nullable=False, default=False)
    first_aid_cert_url = Column(Text)
    police_clearance_url = Column(Text)
    police_clearance_exp = Column(Date)
    verification_status = Column(String, nullable=False, default="pending")
    total_trips = Column(Integer, nullable=False, default=0)
    average_rating = Column(Numeric)
    training_completed = Column(BOOLEAN, nullable=False, default=False)
    training_completed_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class DriverVehicleAssignment(Base):
    __tablename__ = "driver_vehicle_assignments"

    id = Column(String(36), primary_key=True, nullable=False)
    driver_id = Column(String(36), ForeignKey("driver_profiles.id"), nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    is_primary = Column(BOOLEAN, nullable=False, default=False)
    assigned_from = Column(Date)
    assigned_to = Column(Date)
    created_at = Column(DateTime, nullable=False)
