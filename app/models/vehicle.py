from sqlalchemy import (
    BIGINT,
    BOOLEAN,
    Column,
    Date,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
)

from .base import Base


class VehicleAvailability(Base):
    __tablename__ = "vehicle_availability"

    id = Column(String(36), primary_key=True, nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    available_from = Column(Date, nullable=False)
    available_to = Column(Date, nullable=False)
    availability_type = Column(String, nullable=False)
    block_reason = Column(String)
    created_at = Column(DateTime, nullable=False)


class VehicleDocument(Base):
    __tablename__ = "vehicle_documents"

    id = Column(String(36), primary_key=True, nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    document_type = Column(String, nullable=False)
    document_url = Column(Text, nullable=False)
    document_number = Column(String)
    issued_by = Column(String)
    issue_date = Column(Date)
    expiry_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime)
    uploaded_at = Column(DateTime, nullable=False)


class VehicleInspection(Base):
    __tablename__ = "vehicle_inspections"

    id = Column(String(36), primary_key=True, nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    inspection_type = Column(String, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    conducted_date = Column(Date)
    overall_result = Column(String)
    brakes_ok = Column(BOOLEAN)
    engine_ok = Column(BOOLEAN)
    tyres_ok = Column(BOOLEAN)
    seatbelts_ok = Column(BOOLEAN)
    lights_ok = Column(BOOLEAN)
    interior_clean = Column(BOOLEAN)
    ac_ok = Column(BOOLEAN)
    notes = Column(Text)
    required_repairs = Column(Text)
    report_url = Column(Text)
    next_inspection_due = Column(Date)
    created_at = Column(DateTime, nullable=False)


class VehiclePhoto(Base):
    __tablename__ = "vehicle_photos"

    id = Column(String(36), primary_key=True, nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    photo_url = Column(Text, nullable=False)
    photo_data = Column(LargeBinary, nullable=True)
    content_type = Column(String(50), nullable=True)
    photo_type = Column(String, nullable=False)
    is_primary = Column(BOOLEAN, nullable=False, default=False)
    sort_order = Column(SmallInteger)
    uploaded_at = Column(DateTime, nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(SmallInteger, nullable=False)
    color = Column(String, nullable=False)
    registration_plate = Column(String, nullable=False, unique=True)
    vehicle_type = Column(String, nullable=False)
    transmission = Column(String, nullable=False)
    fuel_type = Column(String, nullable=False)
    passenger_capacity = Column(SmallInteger, nullable=False)
    has_ac = Column(BOOLEAN, nullable=False, default=False)
    has_wifi = Column(BOOLEAN, nullable=False, default=False)
    has_child_seat = Column(BOOLEAN, nullable=False, default=False)
    has_roof_rack = Column(BOOLEAN, nullable=False, default=False)
    is_4wd = Column(BOOLEAN, nullable=False, default=False)
    has_gps = Column(BOOLEAN, nullable=False, default=False)
    has_bluetooth = Column(BOOLEAN, nullable=False, default=False)
    has_usb_charger = Column(BOOLEAN, nullable=False, default=False)
    is_pet_friendly = Column(BOOLEAN, nullable=False, default=False)
    description = Column(Text)
    base_daily_rate_ugx = Column(BIGINT, nullable=False)
    status = Column(String, nullable=False)
    rejection_reason = Column(Text)
    service_area = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
