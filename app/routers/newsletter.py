import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.newsletter import NewsletterSubscriber
from app.services import email_service

router = APIRouter(prefix="/newsletter", tags=["newsletter"])
logger = logging.getLogger(__name__)


class SubscribeRequest(BaseModel):
    email: EmailStr


def _send_welcome(email: str) -> None:
    try:
        email_service.send_newsletter_welcome(email)
    except Exception as exc:
        logger.error("Failed to send newsletter welcome to %s: %s", email, exc)


@router.post("/subscribe", status_code=201)
def subscribe(
    payload: SubscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == payload.email
    ).first()

    if existing:
        if existing.is_active:
            return {"message": "You're already subscribed!"}
        existing.is_active = True
        db.commit()
        background_tasks.add_task(_send_welcome, existing.email)
        return {"message": "Welcome back — you've been resubscribed!"}

    subscriber = NewsletterSubscriber(
        id=str(uuid.uuid4()),
        email=payload.email,
        is_active=True,
        subscribed_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(subscriber)
    db.commit()
    background_tasks.add_task(_send_welcome, payload.email)
    return {"message": "Thank you for subscribing! Check your inbox for a welcome email."}


@router.post("/unsubscribe")
def unsubscribe(payload: SubscribeRequest, db: Session = Depends(get_db)):
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == payload.email
    ).first()
    if sub:
        sub.is_active = False
        db.commit()
    return {"message": "You have been unsubscribed."}
