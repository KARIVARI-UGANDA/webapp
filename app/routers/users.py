import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import User
from app.schemas.user import UserRead
from app.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])

UPLOAD_DIR = "uploads/documents"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_language: Optional[str] = None
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="New password must be at least 8 characters"
        )
    current_user.password_hash = hash_password(payload.new_password)
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"message": "Password updated successfully"}


@router.post("/me/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail="File must be JPEG, PNG, WebP, or PDF"
        )
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large — max 10 MB")

    user_dir = os.path.join(UPLOAD_DIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "file")[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(user_dir, filename)
    with open(path, "wb") as f:
        f.write(data)

    url = f"/{path.replace(os.sep, '/')}"
    return {"url": url}


@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Avatar must be JPEG, PNG, or WebP")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large — max 10 MB")

    user_dir = os.path.join(UPLOAD_DIR, current_user.id)
    os.makedirs(user_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "avatar.jpg")[1] or ".jpg"
    filename = f"avatar_{uuid.uuid4()}{ext}"
    path = os.path.join(user_dir, filename)
    with open(path, "wb") as f:
        f.write(data)

    url = f"/{path.replace(os.sep, '/')}"
    current_user.profile_photo_url = url
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
