from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from .base import Base


class TouristKYC(Base):
    __tablename__ = "tourist_kyc"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    document_type = Column(String)           # 'passport' | 'national_id'
    document_number_hash = Column(String)    # one-way hash — never store plaintext
    document_country = Column(String(2))     # ISO 3166-1 alpha-2
    document_expiry = Column(String)         # ISO date
    full_name_on_doc = Column(String)
    date_of_birth = Column(String)           # ISO date; used for age >= 18 check
    provider = Column(String)                # 'onfido' | 'persona' | 'veriff' | 'manual'
    provider_check_id = Column(String)
    provider_status = Column(String)         # raw status from provider
    status = Column(String, nullable=False, default="not_started")
    # not_started | in_progress | approved | rejected | expired | manual_review
    risk_score = Column(Float)               # 0.0–1.0 if provider returns one
    rejection_reason = Column(Text)
    submitted_at = Column(DateTime)
    decided_at = Column(DateTime)
    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
