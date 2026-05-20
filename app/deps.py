from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)] = None,
    db: Session = Depends(get_db),
):
    from app.models import User

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account suspended")

    return user


def require_role(*roles: str):
    def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {', '.join(roles)}",
            )
        return current_user

    return dependency


def require_driver_eligible(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Raises 422 if the driver is not both verified AND training-complete.
    Used by the booking assignment endpoint (Phase 8).
    """
    from app.models.driver import DriverProfile

    if current_user.role != "driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only drivers can use this endpoint")

    profile = db.query(DriverProfile).filter(DriverProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=422, detail="Driver profile not found")
    if profile.verification_status != "verified":
        raise HTTPException(
            status_code=422,
            detail=f"Driver is not verified (status: {profile.verification_status})",
        )
    if not profile.training_completed:
        raise HTTPException(
            status_code=422,
            detail="Driver has not completed all required training modules",
        )
    return current_user


# Typed shorthands used in routers
CurrentUser = Annotated[object, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

