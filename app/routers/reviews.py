from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])

_any_auth = get_current_user


@router.get("/")
def list_reviews(current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 10")


@router.patch("/{review_id}/flag")
def flag_review(review_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 10")
