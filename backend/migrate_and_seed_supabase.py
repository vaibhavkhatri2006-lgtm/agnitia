"""
Script to create all model tables and seed deterministic data to Supabase PostgreSQL.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import engine, SessionLocal, Base
import app.models  # Ensures all models are registered
from seed import seed_database
from sqlalchemy import inspect

def main():
    print("=" * 60)
    print("MIGRATING & SEEDING SUPABASE LIVE DATABASE")
    print("=" * 60)
    print("Target DB Dialect:", engine.dialect.name)
    
    print("\n[Step 1] Creating all tables on Supabase...")
    Base.metadata.create_all(bind=engine)
    print("[SUCCESS] All model tables created.")

    print("\n[Step 2] Seeding initial data on Supabase...")
    db = SessionLocal()
    try:
        counts = seed_database(db)
        print("[SUCCESS] Database seeded successfully.")
        print("\nSeeded Summary:")
        for k, v in counts.items():
            print(f"  - {k}: {v}")
    finally:
        db.close()

    print("\n[Step 3] Verifying public tables on Supabase...")
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema="public")
    print(f"Total tables in public schema: {len(tables)}")
    for t in sorted(tables):
        print(f"  - {t}")

    print("\n[COMPLETE] Supabase database is now completely set up and live!")

if __name__ == "__main__":
    main()
