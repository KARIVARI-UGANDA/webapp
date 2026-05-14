from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/")
def read_admin():
    return {"message": "Admin router is available"}
