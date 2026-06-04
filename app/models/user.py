from sqlalchemy import BOOLEAN, Column, Date, DateTime, ForeignKey, String, Text
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    profile_photo_url = Column(Text)
    preferred_language = Column(String)
    bio = Column(Text)
    is_verified = Column(BOOLEAN, nullable=False, default=False)
    is_active = Column(BOOLEAN, nullable=False, default=True)
    account_type = Column(String, nullable=False)
    corporate_id = Column(String(36), ForeignKey("corporate_accounts.id"), nullable=True)
    two_fa_enabled = Column(BOOLEAN, nullable=False, default=False)
    two_fa_secret = Column(String)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime)


class UserIdentityVerification(Base):
    __tablename__ = "user_identity_verifications"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False)
    document_number = Column(String, nullable=False)
    document_front_url = Column(Text, nullable=False)
    document_back_url = Column(Text)
    selfie_url = Column(Text)
    expiry_date = Column(Date)
    verification_status = Column(String, nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text)
    submitted_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False)
    device_info = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
