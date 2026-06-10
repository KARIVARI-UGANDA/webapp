"""
Seed demo accounts into the database.
Run once after the app has started:

    python seed.py

Safe to re-run — skips accounts that already exist.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure app is importable
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models as _  # registers all models
from app.models.user import User
from app.security import hash_password

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set.")
    sys.exit(1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
Session = sessionmaker(bind=engine)

DEMO_USERS = [
    {
        "full_name": "Super Admin",
        "email": "george.mutale345@stud.th-deg.de",
        "phone_number": "+256700000001",
        "password": "Administer01@#",
        "role": "admin",
        "account_type": "individual",
    },
    {
        "full_name": "Admin Operator",
        "email": "mutalegeorge367@gmail.com",
        "phone_number": "+256700000002",
        "password": "Operator02@#",
        "role": "admin",
        "account_type": "individual",
    },
    {
        "full_name": "Demo Customer",
        "email": "george.mutale@stud.th-deg.de",
        "phone_number": "+256700000003",
        "password": "Tourist01@#",
        "role": "customer",
        "account_type": "individual",
    },
]

now = datetime.now(timezone.utc).replace(tzinfo=None)

with Session() as db:
    created = 0
    for u in DEMO_USERS:
        exists = db.query(User).filter(User.email == u["email"]).first()
        if exists:
            print(f"  skip  {u['email']} (already exists)")
            continue
        user = User(
            id=str(uuid.uuid4()),
            full_name=u["full_name"],
            email=u["email"],
            phone_number=u["phone_number"],
            password_hash=hash_password(u["password"]),
            role=u["role"],
            account_type=u["account_type"],
            is_verified=True,
            is_active=True,
            two_fa_enabled=False,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        created += 1
        print(f"  ✅ created  {u['role']:10}  {u['email']}")
    db.commit()

print(f"\n  Done — {created} account(s) created.\n")
