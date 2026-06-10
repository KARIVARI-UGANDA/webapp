"""
Entry point — works both locally (python run.py) and inside Docker.

  Local:  python run.py
  Docker: docker compose up --build
"""

import os
import sys
import time

import uvicorn


def _wait_for_db(url: str, retries: int = 20, delay: float = 2.0) -> None:
    """Block until Postgres is ready (skip for SQLite)."""
    if not url.startswith("postgresql"):
        return
    try:
        import sqlalchemy

        engine = sqlalchemy.create_engine(url)
        for attempt in range(1, retries + 1):
            try:
                with engine.connect():
                    print(f"[run.py] Database ready.")
                    return
            except Exception:
                print(f"[run.py] Waiting for database… ({attempt}/{retries})")
                time.sleep(delay)
        print("[run.py] ERROR: Could not connect to the database. Exiting.")
        sys.exit(1)
    except ImportError:
        pass  # sqlalchemy not available at check time — let the app fail naturally


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("[run.py] ERROR: DATABASE_URL is not set.")
        print("  Run with Docker:  docker compose up --build")
        print("  Run locally:      set DATABASE_URL=sqlite:///./karivari.db && python run.py")
        sys.exit(1)

    _wait_for_db(db_url)

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("UVICORN_RELOAD", "0") == "1"

    print(f"[run.py] Starting Karivari Uganda on http://{host}:{port}")
    print(f"[run.py] API docs:  http://{host}:{port}/api/docs")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=["app"] if reload else None,
    )
