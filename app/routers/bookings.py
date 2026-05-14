from fastapi import APIRouter

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get("/")
def read_bookings():
    return {"message": "Bookings router is available"}
