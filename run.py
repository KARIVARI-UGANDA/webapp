"""
Single entry point — handles everything automatically:
  1. Installs dependencies
  2. Waits for the database
  3. Creates all tables
  4. Seeds demo accounts (skips if they already exist)
  5. Starts the web server

Usage:
  Codespaces / local:   python run.py
  Docker:               docker compose up --build   (calls this automatically)
"""

import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone


# ── Step 1: install dependencies ──────────────────────────────────────────────
def _install():
    req = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req):
        return
    print("[startup] Installing dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", req, "-q"],
        stdout=subprocess.DEVNULL,
    )


_install()


# ── Step 2: resolve DATABASE_URL ──────────────────────────────────────────────
from dotenv import load_dotenv  # noqa: E402  (needs pip install first)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default to local SQLite so `python run.py` works with zero config
    DATABASE_URL = "sqlite:///./karivari.db"
    os.environ["DATABASE_URL"] = DATABASE_URL
    print(f"[startup] No DATABASE_URL set — using SQLite: {DATABASE_URL}")

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "local-dev-secret-change-in-production-32c"


# ── Step 3: wait for Postgres ─────────────────────────────────────────────────
def _wait_for_db(url: str, retries: int = 30, delay: float = 2.0) -> None:
    if not url.startswith("postgresql"):
        return
    import sqlalchemy

    engine = sqlalchemy.create_engine(url)
    for attempt in range(1, retries + 1):
        try:
            with engine.connect():
                print("[startup] Database is ready.")
                return
        except Exception:
            print(f"[startup] Waiting for database… ({attempt}/{retries})")
            time.sleep(delay)
    print("[startup] ERROR: Could not connect to the database.")
    sys.exit(1)


_wait_for_db(DATABASE_URL)


# ── Step 4: create tables ─────────────────────────────────────────────────────
print("[startup] Creating database tables...")
import app.models as _models  # noqa: E402  registers all ORM classes
from sqlalchemy import create_engine as _ce  # noqa: E402
from app.models.base import Base  # noqa: E402

_engine = _ce(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
Base.metadata.create_all(bind=_engine)


# ── Step 5: seed demo accounts ────────────────────────────────────────────────
from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402

_Session = sessionmaker(bind=_engine)

DEMO_USERS = [
    {
        "full_name": "Super Admin",
        "email": "george.mutale345@stud.th-deg.de",
        "phone_number": "+256700000001",
        "password": "Administer01@#",
        "role": "admin",
    },
    {
        "full_name": "Admin Operator",
        "email": "mutalegeorge367@gmail.com",
        "phone_number": "+256700000002",
        "password": "Operator02@#",
        "role": "admin",
    },
    {
        "full_name": "Demo Customer",
        "email": "george.mutale@stud.th-deg.de",
        "phone_number": "+256700000003",
        "password": "Tourist01@#",
        "role": "customer",
    },
]

from sqlalchemy.exc import IntegrityError  # noqa: E402

now = datetime.now(timezone.utc).replace(tzinfo=None)
seeded = 0
for u in DEMO_USERS:
    with _Session() as _db:
        try:
            exists = (
                _db.query(User)
                .filter(
                    (User.email == u["email"]) | (User.phone_number == u["phone_number"])
                )
                .first()
            )
            if not exists:
                _db.add(User(
                    id=str(uuid.uuid4()),
                    full_name=u["full_name"],
                    email=u["email"],
                    phone_number=u["phone_number"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    account_type="individual",
                    is_verified=True,
                    is_active=True,
                    two_fa_enabled=False,
                    created_at=now,
                    updated_at=now,
                ))
                _db.commit()
                seeded += 1
        except IntegrityError:
            _db.rollback()
if seeded:
    print(f"[startup] Seeded {seeded} demo account(s).")


# ── Step 6: start the server ──────────────────────────────────────────────────
import uvicorn  # noqa: E402

host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", "8000"))

print()
print("  Kari Vari Uganda is running!")
print(f"  App:      http://localhost:{port}")
print(f"  API docs: http://localhost:{port}/api/docs")
print()
print("  Demo accounts:")
print("  Super Admin  george.mutale345@stud.th-deg.de  /  Administer01@#")
print("  Admin        mutalegeorge367@gmail.com        /  Operator02@#")
print("  Customer     george.mutale@stud.th-deg.de     /  Tourist01@#")
print()

uvicorn.run(
    "app.main:app",
    host=host,
    port=port,
    reload=os.getenv("UVICORN_RELOAD", "0") == "1",
    reload_dirs=["app"] if os.getenv("UVICORN_RELOAD", "0") == "1" else None,
)
