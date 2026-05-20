from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

_any_auth = get_current_user


@router.patch("/{message_id}/read")
def mark_message_read(message_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 11")
