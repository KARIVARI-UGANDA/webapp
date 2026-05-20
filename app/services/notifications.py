import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Notification


def create_notification(
    db: Session,
    *,
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
) -> Notification:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        notification_type=notification_type,
        channel="in_app",
        title=title,
        body=body,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        is_read=False,
        created_at=now,
    )
    db.add(notif)
    # caller is responsible for db.commit()
    return notif
