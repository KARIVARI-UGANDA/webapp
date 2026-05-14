from fastapi import APIRouter

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/")
def read_payments():
    return {"message": "Payments router is available"}
