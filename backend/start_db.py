import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import check_database_connection


def main():
    print("============================================================")
    print("CivicPulse Database Starter & Connection Verifier")
    from sqlalchemy.engine import make_url
    safe_url = make_url(settings.DATABASE_URL).render_as_string(hide_password=True)
    print(f"Target Database URL: {safe_url}")
    print("Attempting connection probe (SELECT 1)...")

    status = check_database_connection()
    if status.get("status") == "connected":
        print("[SUCCESS] Database connection established successfully!")
        print(f"Database Dialect: {status.get('dialect')}")
        print("Database is ready for CivicPulse services.")
        sys.exit(0)
    else:
        print("[FAIL] Database connection could not be established.")
        print(f"Error Details: {status.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
