from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

_any_auth = get_current_user


# POST /api/payments/initiate  — tourist initiates checkout
@router.post("/initiate")
def initiate_payment(current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 9")


# POST /api/payments/webhook  — provider callback (no JWT, signature-verified)
@router.post("/webhook")
async def payment_webhook(request: Request):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 9")


# GET /api/payments/{booking_id}/status
@router.get("/{booking_id}/status")
def payment_status(booking_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 9")
