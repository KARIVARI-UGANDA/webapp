import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.models.kyc import PasswordResetToken, RefreshToken
from app.schemas.auth import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
import logging
from app.services import email_service
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _issue_token_pair(user: User, db: Session) -> dict:
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    token_hash = hash_password(refresh_token)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(days=14)

    rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=now,
    )
    db.add(rt)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "full_name": user.full_name,
    }


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.phone_number and db.query(User).filter(User.phone_number == payload.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(
        id=str(uuid.uuid4()),
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=payload.role,
        account_type="individual",
        preferred_language=payload.preferred_language or "en",
        is_verified=False,
        is_active=True,
        two_fa_enabled=False,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="An account with these details already exists") from e

    return _issue_token_pair(user, db)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account suspended")

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)

    return _issue_token_pair(user, db)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = token_data.get("sub")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stored_tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .all()
    )

    matched = next(
        (t for t in stored_tokens if verify_password(payload.refresh_token, t.token_hash)), None
    )
    if not matched:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or suspended")

    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    user_id = token_data.get("sub")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stored_tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .all()
    )

    for t in stored_tokens:
        if verify_password(payload.refresh_token, t.token_hash):
            t.revoked_at = now
            db.add(t)
            break

    db.commit()
    return {"message": "Logged out"}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that email address.")

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    prt = PasswordResetToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_password(raw_token),
        expires_at=now + timedelta(hours=1),
        created_at=now,
    )
    db.add(prt)
    db.commit()
    try:
        email_service.send_password_reset(user.email, user.full_name, raw_token)
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", user.email, exc)
    return {"message": "Reset link sent! Check your inbox."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    candidates = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .all()
    )

    matched = next(
        (t for t in candidates if verify_password(payload.token, t.token_hash)), None
    )
    if not matched:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == matched.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    user.updated_at = now
    matched.used_at = now
    db.add(user)
    db.add(matched)
    db.commit()

    return {"message": "Password updated successfully"}


# ── Prototype Dev Sign-in ─────────────────────────────────────────────────────
# Grants instant access for demo/prototype purposes. Remove before production.

_DEV_ACCOUNTS = {
    "customer": {
        "email":      "demo.customer@karivari.ug",
        "password":   "demo_customer_2024",
        "full_name":  "Demo Customer",
        "phone_number": "+256700000001",
        "account_type": "individual",
    },
    "owner": {
        "email":      "demo.owner@karivari.ug",
        "password":   "demo_owner_2024",
        "full_name":  "Demo Car Owner",
        "phone_number": "+256700000002",
        "account_type": "individual",
    },
    "admin": {
        "email":      "demo.admin@karivari.ug",
        "password":   "demo_admin_2024",
        "full_name":  "Demo Admin",
        "phone_number": "+256700000003",
        "account_type": "individual",
    },
}


@router.post("/dev-signin")
def dev_signin(role: str = "customer", db: Session = Depends(get_db)):
    """Prototype-only: provision a demo account and return tokens. Remove before production."""
    allowed = {"customer", "owner", "admin"}
    if role not in allowed:
        raise HTTPException(status_code=400, detail=f"role must be one of {allowed}")

    cfg = _DEV_ACCOUNTS[role]

    # Find or create the demo user
    user = db.query(User).filter(User.email == cfg["email"]).first()
    if not user:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        user = User(
            id=str(uuid.uuid4()),
            email=cfg["email"],
            password_hash=hash_password(cfg["password"]),
            full_name=cfg["full_name"],
            phone_number=cfg["phone_number"],
            role=role,
            account_type=cfg["account_type"],
            is_verified=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.email == cfg["email"]).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="Demo account unavailable")

    return _issue_token_pair(user, db)
