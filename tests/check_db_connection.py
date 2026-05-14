import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from app.database import engine
import sqlalchemy


def test_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text("SELECT 1"))
            value = result.scalar()
            print("Database connection successful. SELECT 1 returned:", value)
    except Exception as error:
        print("Database connection failed:", error)
        raise


if __name__ == "__main__":
    test_db_connection()
