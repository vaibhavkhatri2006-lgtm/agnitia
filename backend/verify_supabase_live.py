"""
CivicPulse - Complete Supabase Live Database Verification Script
Verifies all tables, ORM models, relationships, and queries directly on Supabase PostgreSQL.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text
from app.config import settings
from app.database import engine, SessionLocal
from app.models import (
    Base,
    DataSource,
    GeographicArea,
    ServiceCategory,
    Service,
    ServiceCapacity,
    PopulationCell,
    CommunityReport,
    ReportVerification,
    AuditLog,
    Role,
    Permission,
    User,
)

def verify_supabase():
    print("=" * 70)
    print("CIVICPULSE - SUPABASE LIVE DATABASE & ORM MODELS VERIFICATION")
    print("=" * 70)
    
    # 1. Connection check
    print(f"\n[1] Connection Dialect: {engine.dialect.name}")
    inspector = inspect(engine)
    public_tables = sorted(inspector.get_table_names(schema="public"))
    print(f"[1] Public Tables in Supabase ({len(public_tables)} found):")
    for tbl in public_tables:
        print(f"    - {tbl}")

    required_tables = [
        "alembic_version",
        "data_sources",
        "service_categories",
        "geographic_areas",
        "population_cells",
        "services",
        "service_capacities",
        "community_reports",
        "report_verifications",
        "roles",
        "permissions",
        "role_permissions",
        "users",
        "audit_logs",
    ]
    missing = [t for t in required_tables if t not in public_tables]
    if missing:
        print(f"\n[ERROR] Missing tables in Supabase: {missing}")
        return False
    else:
        print("\n[PASS] All required application tables exist in Supabase 'public' schema.")

    # 2. Row Counts & Data Integrity
    db = SessionLocal()
    try:
        print("\n[2] Entity Counts in Supabase:")
        counts = {
            "Data Sources": db.query(DataSource).count(),
            "Service Categories": db.query(ServiceCategory).count(),
            "Geographic Areas": db.query(GeographicArea).count(),
            "Population Cells": db.query(PopulationCell).count(),
            "Services": db.query(Service).count(),
            "Service Capacities": db.query(ServiceCapacity).count(),
            "Community Reports": db.query(CommunityReport).count(),
            "Report Verifications": db.query(ReportVerification).count(),
            "Roles": db.query(Role).count(),
            "Permissions": db.query(Permission).count(),
            "Users": db.query(User).count(),
            "Audit Logs": db.query(AuditLog).count(),
        }
        for name, count in counts.items():
            print(f"    - {name:<22}: {count}")
            assert count > 0, f"{name} is empty!"
        print("[PASS] All models have live data populated in Supabase.")

        # 3. Model Relationship Traversal
        print("\n[3] Model Relationship Verification:")
        # Test User -> Role -> Permissions
        admin_user = db.query(User).filter_by(email="admin@example.com").first()
        assert admin_user is not None, "Admin user not found"
        print(f"    - User '{admin_user.email}' loaded successfully.")
        print(f"      Role: {admin_user.role.name}")
        print(f"      Permissions: {[p.code for p in admin_user.role.permissions]}")

        # Test GeographicArea -> Services -> ServiceCategory
        city = db.query(GeographicArea).filter_by(name="Indore").first()
        assert city is not None, "Indore city record not found"
        print(f"    - Geographic Root: '{city.name}' (Area Type: {city.area_type})")
        
        # Test Services with Capacities
        hospital = db.query(Service).filter(Service.name.like("%Hospital%")).first()
        if hospital:
            print(f"    - Service '{hospital.name}' (Status: {hospital.status})")
            print(f"      Category: {hospital.category.name if hospital.category else 'None'}")
            print(f"      Capacity: {hospital.capacity_record.capacity if hospital.capacity_record else 'None'}")

        # 4. Check Alembic Migration Revision in DB
        with engine.connect() as conn:
            rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            print(f"\n[4] Alembic Migration Version in Supabase: {rev}")

        print("\n" + "=" * 70)
        print("RESULT: COMPLETE DATABASE AND ALL MODELS ARE FULLY LIVE ON SUPABASE!")
        print("=" * 70)
        return True
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_supabase()
    if not success:
        sys.exit(1)
