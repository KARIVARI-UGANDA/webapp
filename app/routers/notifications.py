from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

_any_auth = get_current_user


@router.get("/")
def list_notifications(current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 12")


@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 12")


@router.post("/read-all")
def mark_all_read(current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 12")
