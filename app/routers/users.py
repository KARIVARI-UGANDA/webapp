# generate route for users
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session      
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead
from app.utils import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing
    hashed_password = hash_password(user.password)
    
    # Create new user instance
    new_user = User(
        id=str(uuid.uuid4()),
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        password_hash=hashed_password,
        role=user.role,
        account_type=user.account_type,
        profile_photo_url=user.profile_photo_url,
        preferred_language=user.preferred_language,
        corporate_id=user.corporate_id,
        two_fa_enabled=user.two_fa_enabled,
        two_fa_secret=user.two_fa_secret,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add to database and commit
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


