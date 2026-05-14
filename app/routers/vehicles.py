from fastapi import APIRouter

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.get("/")
def read_vehicles():
    return {"message": "Vehicles router is available"}
