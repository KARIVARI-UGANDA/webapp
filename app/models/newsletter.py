from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.models.base import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subscribed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
