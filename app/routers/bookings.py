from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user, require_role

router = APIRouter(prefix="/bookings", tags=["bookings"])

_tourist = require_role("tourist")
_driver = require_role("driver")
_admin = require_role("admin")
_any_auth = get_current_user


# POST /api/bookings  — tourist creates booking (KYC gate enforced in Phase 8)
@router.post("/")
def create_booking(current_user=Depends(_tourist)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# GET /api/bookings  — role-filtered list
@router.get("/")
def list_bookings(current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# GET /api/bookings/{id}
@router.get("/{booking_id}")
def get_booking(booking_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# PATCH /api/bookings/{id}/cancel
@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# PATCH /api/bookings/{id}/assign-driver  — admin
@router.patch("/{booking_id}/assign-driver")
def assign_driver(booking_id: str, current_user=Depends(_admin)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# PATCH /api/bookings/{id}/respond  — driver accepts/declines assignment
@router.patch("/{booking_id}/respond")
def respond_to_assignment(booking_id: str, current_user=Depends(_driver)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# PATCH /api/bookings/{id}/start  — driver marks trip in_progress
@router.patch("/{booking_id}/start")
def start_trip(booking_id: str, current_user=Depends(_driver)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# PATCH /api/bookings/{id}/complete  — driver marks trip completed
@router.patch("/{booking_id}/complete")
def complete_trip(booking_id: str, current_user=Depends(_driver)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 8")


# POST /api/bookings/{id}/review  — tourist reviews completed trip
@router.post("/{booking_id}/review")
def create_review(booking_id: str, current_user=Depends(_tourist)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 10")


# GET /api/bookings/{id}/messages
@router.get("/{booking_id}/messages")
def list_messages(booking_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 11")


# POST /api/bookings/{id}/messages
@router.post("/{booking_id}/messages")
def send_message(booking_id: str, current_user=Depends(_any_auth)):
    raise HTTPException(status_code=501, detail="Not implemented yet — Phase 11")
