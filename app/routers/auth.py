from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/")
def read_auth():
    return {"message": "Auth router is available"}
