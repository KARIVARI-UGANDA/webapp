import os
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, conn_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass


def run_migrations():
    """Add columns that may be missing on an existing database (safe to re-run)."""
    # Only applies to PostgreSQL — SQLite uses a different syntax and these
    # columns are created automatically via create_all on a fresh DB.
    if not DATABASE_URL.startswith("postgresql"):
        return
    migrations = [
        "ALTER TABLE vehicle_photos ADD COLUMN IF NOT EXISTS photo_data BYTEA",
        "ALTER TABLE vehicle_photos ADD COLUMN IF NOT EXISTS content_type VARCHAR(50)",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS has_gps BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS has_bluetooth BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS has_usb_charger BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS is_pet_friendly BOOLEAN NOT NULL DEFAULT FALSE",
        """CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id VARCHAR PRIMARY KEY,
            email VARCHAR UNIQUE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            subscribed_at TIMESTAMP NOT NULL DEFAULT NOW()
        )""",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(__import__("sqlalchemy").text(sql))
            except Exception:
                pass
        conn.commit()


run_migrations()
