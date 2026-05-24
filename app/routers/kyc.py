from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import UserIdentityVerification

router = APIRouter(prefix="/kyc", tags=["kyc"])

_any_auth = get_current_user


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class KYCSubmit(BaseModel):
    document_type: str          # passport | national_id | driving_licence
    document_number: str
    document_front_url: str
    document_back_url: Optional[str] = None
    selfie_url: Optional[str] = None
    expiry_date: Optional[str] = None  # YYYY-MM-DD


@router.get("/me")
def get_kyc_status(current_user=Depends(_any_auth), db: Session = Depends(get_db)):
    record = db.query(UserIdentityVerification).filter(
        UserIdentityVerification.user_id == current_user.id
    ).order_by(UserIdentityVerification.submitted_at.desc()).first()
    if not record:
        return {"status": "not_submitted", "document_type": None}
    return {
        "status": record.verification_status,
        "document_type": record.document_type,
        "document_number": record.document_number,
        "document_front_url": record.document_front_url,
        "document_back_url": record.document_back_url,
        "selfie_url": record.selfie_url,
        "expiry_date": record.expiry_date,
        "submitted_at": record.submitted_at,
        "reviewed_at": record.reviewed_at,
        "rejection_reason": record.rejection_reason,
    }


@router.post("/me/submit")
def submit_kyc_manual(
    payload: KYCSubmit,
    current_user=Depends(_any_auth),
    db: Session = Depends(get_db),
):
    import uuid
    existing = db.query(UserIdentityVerification).filter(
        UserIdentityVerification.user_id == current_user.id
    ).first()

    now = _now()
    if existing:
        existing.document_type = payload.document_type
        existing.document_number = payload.document_number
        existing.document_front_url = payload.document_front_url
        existing.document_back_url = payload.document_back_url
        existing.selfie_url = payload.selfie_url
        existing.expiry_date = payload.expiry_date
        existing.verification_status = "pending"
        existing.submitted_at = now
        db.commit()
        return {"message": "Identity document updated and submitted for review", "status": "pending"}

    record = UserIdentityVerification(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        document_type=payload.document_type,
        document_number=payload.document_number,
        document_front_url=payload.document_front_url,
        document_back_url=payload.document_back_url,
        selfie_url=payload.selfie_url,
        expiry_date=payload.expiry_date,
        verification_status="pending",
        submitted_at=now,
    )
    db.add(record)
    db.commit()
    return {"message": "Identity document submitted for review", "status": "pending"}


@router.post("/webhook")
async def kyc_webhook(request: Request):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")
