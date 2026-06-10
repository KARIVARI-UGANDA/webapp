from sqlalchemy import BIGINT, BOOLEAN, Column, DateTime, ForeignKey, String, Text

from .base import Base


class CorporateAccount(Base):
    __tablename__ = "corporate_accounts"

    id = Column(String(36), primary_key=True, nullable=False)
    company_name = Column(String, nullable=False)
    registration_number = Column(String, unique=True)
    tax_id = Column(String)
    billing_email = Column(String, nullable=False)
    billing_phone = Column(String)
    billing_address = Column(Text)
    monthly_limit_ugx = Column(BIGINT)
    primary_contact_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_active = Column(BOOLEAN, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)
