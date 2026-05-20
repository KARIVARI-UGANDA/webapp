from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import require_role

router = APIRouter(prefix="/kyc", tags=["kyc"])

_tourist = require_role("tourist")


@router.get("/me")
def get_kyc_status(current_user=Depends(_tourist)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


@router.post("/me/initiate")
def initiate_kyc(current_user=Depends(_tourist)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


@router.post("/me/submit")
def submit_kyc_manual(current_user=Depends(_tourist)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")


@router.post("/webhook")
async def kyc_webhook(request: Request):
    # No auth — signature-verified by provider
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 7")
