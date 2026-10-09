"""
CivicPulse Deterministic Seed Script
Stage 1: Database + Demo Data

Populates the database with realistic, deterministic simulated data.
All demo data is labeled with source_type='simulated_demo'.
"""
import sys
import json
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import (
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
from app.core.security import hash_password


def seed_database(db: Session) -> dict:
    """Executes deterministic seeding. Idempotent and reproducible."""
    print("Beginning deterministic seeding...")
    Base.metadata.create_all(bind=db.get_bind())

    # 1. DATA SOURCES
    data_sources_data = [
        {"code": "simulated_demo", "name": "Simulated Demo Dataset", "description": "Synthetic data generated for development and simulation testing", "trust_level": 0.70},
        {"code": "osm", "name": "OpenStreetMap", "description": "Community geospatial data", "trust_level": 0.85},
        {"code": "government", "name": "Municipal Government Authority", "description": "Official city data records", "trust_level": 0.95},
        {"code": "community", "name": "Community Civic Reports", "description": "Citizen reported observations and alerts", "trust_level": 0.75},
        {"code": "admin", "name": "Platform Administrator", "description": "Direct administrative interventions", "trust_level": 1.00},
    ]

    for item in data_sources_data:
        existing = db.query(DataSource).filter_by(code=item["code"]).first()
        if not existing:
            db.add(DataSource(**item))
    db.flush()

    # 2. SERVICE CATEGORIES
    categories_data = [
        {"code": "healthcare", "name": "Healthcare", "description": "Hospitals, clinics, and emergency medical stations", "icon": "hospital"},
        {"code": "education", "name": "Education", "description": "Primary schools, secondary schools, and learning centers", "icon": "school"},
        {"code": "transport", "name": "Transport", "description": "Transit stations, bus terminals, and multimodal mobility hubs", "icon": "bus"},
        {"code": "water", "name": "Water & Sanitation", "description": "Clean water points, boreholes, and purification stations", "icon": "droplet"},
        {"code": "market", "name": "Food & Market", "description": "Essential public markets and grocery distribution centers", "icon": "shopping-cart"},
    ]

    for item in categories_data:
        existing = db.query(ServiceCategory).filter_by(code=item["code"]).first()
        if not existing:
            db.add(ServiceCategory(**item))
    db.flush()

    cat_map = {c.code: c.id for c in db.query(ServiceCategory).all()}

    # 3. GEOGRAPHIC AREAS (Hierarchy: City -> Districts -> Neighbourhoods)
    # City root: Indore, Madhya Pradesh
    city = db.query(GeographicArea).filter_by(name="Indore").first()
    if not city:
        # Check if old Metro City exists to migrate/reuse or create fresh
        old_city = db.query(GeographicArea).filter_by(name="Metro City").first()
        if old_city:
            city = old_city
            city.name = "Indore"
            city.geometry = "MULTIPOLYGON (((75.8000 22.6500, 75.9300 22.6500, 75.9300 22.7800, 75.8000 22.7800, 75.8000 22.6500)))"
            db.flush()
        else:
            city = GeographicArea(
                name="Indore",
                area_type="city",
                parent_id=None,
                population=72000,
                geometry="MULTIPOLYGON (((75.8000 22.6500, 75.9300 22.6500, 75.9300 22.7800, 75.8000 22.7800, 75.8000 22.6500)))",
            )
            db.add(city)
            db.flush()

    # Districts / Wards (Indore administrative zones)
    districts = {
        "Zone 1 - Rajwada Central": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 37000,
            "geometry": "MULTIPOLYGON (((75.8450 22.7100, 75.8650 22.7100, 75.8650 22.7300, 75.8450 22.7300, 75.8450 22.7100)))",
        },
        "Zone 2 - Palasia East": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 18000,
            "geometry": "MULTIPOLYGON (((75.8750 22.7150, 75.9000 22.7150, 75.9000 22.7350, 75.8750 22.7350, 75.8750 22.7150)))",
        },
        "Zone 3 - Vijay Nagar North": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 22000,
            "geometry": "MULTIPOLYGON (((75.8800 22.7400, 75.9150 22.7400, 75.9150 22.7650, 75.8800 22.7650, 75.8800 22.7400)))",
        },
        "Zone 4 - Bhanwarkuan South": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 15000,
            "geometry": "MULTIPOLYGON (((75.8500 22.6800, 75.8750 22.6800, 75.8750 22.7050, 75.8500 22.7050, 75.8500 22.6800)))",
        },
    }

    # Name mapping for seamless update of existing data if needed
    legacy_district_map = {
        "District 1 - Central Ward": "Zone 1 - Rajwada Central",
        "District 2 - Riverside North": "Zone 2 - Palasia East",
        "District 3 - Highlands East": "Zone 3 - Vijay Nagar North",
        "District 4 - Southern Outskirts": "Zone 4 - Bhanwarkuan South",
    }
    for old_dname, new_dname in legacy_district_map.items():
        old_rec = db.query(GeographicArea).filter_by(name=old_dname).first()
        if old_rec and not db.query(GeographicArea).filter_by(name=new_dname).first():
            old_rec.name = new_dname
            old_rec.geometry = districts[new_dname]["geometry"]
            db.flush()

    dist_map = {}
    for name, data in districts.items():
        existing = db.query(GeographicArea).filter_by(name=name).first()
        if not existing:
            existing = GeographicArea(name=name, **data)
            db.add(existing)
            db.flush()
        dist_map[name] = existing.id

    # Neighbourhoods (Prominent Indore localities)
    neighbourhoods = {
        "Rajwada": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["Zone 1 - Rajwada Central"],
            "population": 25000,
            "geometry": "MULTIPOLYGON (((75.8520 22.7150, 75.8620 22.7150, 75.8620 22.7240, 75.8520 22.7240, 75.8520 22.7150)))",
        },
        "Sarafa": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["Zone 1 - Rajwada Central"],
            "population": 12000,
            "geometry": "MULTIPOLYGON (((75.8460 22.7140, 75.8520 22.7140, 75.8520 22.7210, 75.8460 22.7210, 75.8460 22.7140)))",
        },
        "Old Palasia": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["Zone 2 - Palasia East"],
            "population": 18000,
            "geometry": "MULTIPOLYGON (((75.8900 22.7180, 75.9080 22.7180, 75.9080 22.7320, 75.8900 22.7320, 75.8900 22.7180)))",
        },
        "Vijay Nagar": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["Zone 3 - Vijay Nagar North"],
            "population": 22000,
            "geometry": "MULTIPOLYGON (((75.8860 22.7450, 75.9080 22.7450, 75.9080 22.7620, 75.8860 22.7620, 75.8860 22.7450)))",
        },
        "Bhanwarkuan": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["Zone 4 - Bhanwarkuan South"],
            "population": 15000,
            "geometry": "MULTIPOLYGON (((75.8500 22.6950, 75.8650 22.6950, 75.8650 22.7080, 75.8500 22.7080, 75.8500 22.6950)))",
        },
    }

    legacy_neigh_map = {
        "Downtown Core": "Rajwada",
        "West End": "Sarafa",
        "Riverside Commons": "Old Palasia",
        "Highlands Valley": "Vijay Nagar",
        "South Hillside": "Bhanwarkuan",
    }
    for old_nname, new_nname in legacy_neigh_map.items():
        old_nrec = db.query(GeographicArea).filter_by(name=old_nname).first()
        if old_nrec and not db.query(GeographicArea).filter_by(name=new_nname).first():
            old_nrec.name = new_nname
            old_nrec.geometry = neighbourhoods[new_nname]["geometry"]
            old_nrec.parent_id = neighbourhoods[new_nname]["parent_id"]
            db.flush()

    neigh_map = {}
    for name, data in neighbourhoods.items():
        existing = db.query(GeographicArea).filter_by(name=name).first()
        if not existing:
            existing = GeographicArea(name=name, **data)
            db.add(existing)
            db.flush()
        else:
            existing.geometry = data["geometry"]
            db.flush()
        neigh_map[name] = existing.id

    # 4. POPULATION CELLS (Fine-grained Demographic breakdown with Indore coordinates)
    cells_data = [
        {
            "area_id": neigh_map["Rajwada"],
            "population": 15000,
            "geometry": "POLYGON ((75.8530 22.7160, 75.8600 22.7160, 75.8600 22.7220, 75.8530 22.7220, 75.8530 22.7160))",
            "demographics": json.dumps({"median_age": 32, "vulnerability_index": 0.20, "child_dependency": 0.15, "elderly_ratio": 0.10}),
        },
        {
            "area_id": neigh_map["Rajwada"],
            "population": 10000,
            "geometry": "POLYGON ((75.8550 22.7180, 75.8620 22.7180, 75.8620 22.7240, 75.8550 22.7240, 75.8550 22.7180))",
            "demographics": json.dumps({"median_age": 34, "vulnerability_index": 0.22, "child_dependency": 0.18, "elderly_ratio": 0.11}),
        },
        {
            "area_id": neigh_map["Vijay Nagar"],
            "population": 22000,
            "geometry": "POLYGON ((75.8880 22.7470, 75.9050 22.7470, 75.9050 22.7600, 75.8880 22.7600, 75.8880 22.7470))",
            "demographics": json.dumps({"median_age": 28, "vulnerability_index": 0.68, "child_dependency": 0.35, "elderly_ratio": 0.18}),
        },
        {
            "area_id": neigh_map["Bhanwarkuan"],
            "population": 15000,
            "geometry": "POLYGON ((75.8520 22.6960, 75.8640 22.6960, 75.8640 22.7070, 75.8520 22.7070, 75.8520 22.6960))",
            "demographics": json.dumps({"median_age": 31, "vulnerability_index": 0.74, "child_dependency": 0.38, "elderly_ratio": 0.21}),
        },
    ]

    for cell in cells_data:
        existing = db.query(PopulationCell).filter_by(area_id=cell["area_id"], population=cell["population"]).first()
        if not existing:
            db.add(PopulationCell(**cell, source_type="simulated_demo"))
    db.flush()

    # 5. SERVICES & CAPACITIES (Real Indore landmarks and facilities)
    # Variation:
    # - Vijay Nagar has NO clinic/hospital (critical healthcare desert)
    # - Bhanwarkuan has BRTS bus point temporarily unavailable (poor transport access)
    # - Palasia health center is overloaded
    services_data = [
        # Healthcare
        {
            "name": "MY Hospital Indore",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["Rajwada"],
            "latitude": 22.7160,
            "longitude": 75.8680,
            "geometry": "POINT (75.8680 22.7160)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.98,
            "operating_hours": "24/7 Emergency & Inpatient",
            "capacity": 500,
            "current_load": 380,
            "cap_status": "normal",
        },
        {
            "name": "Sarafa Community Dispensary",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["Sarafa"],
            "latitude": 22.7172,
            "longitude": 75.8510,
            "geometry": "POINT (75.8510 22.7172)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.92,
            "operating_hours": "Mon-Sat 08:00-18:00",
            "capacity": 80,
            "current_load": 75,
            "cap_status": "constrained",
        },
        {
            "name": "Palasia Health Center",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["Old Palasia"],
            "latitude": 22.7250,
            "longitude": 75.8990,
            "geometry": "POINT (75.8990 22.7250)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.95,
            "operating_hours": "Mon-Fri 08:00-20:00",
            "capacity": 60,
            "current_load": 72,  # Overloaded!
            "cap_status": "overloaded",
        },
        # Education
        {
            "name": "Rajwada Central School",
            "category_id": cat_map["education"],
            "area_id": neigh_map["Rajwada"],
            "latitude": 22.7190,
            "longitude": 75.8570,
            "geometry": "POINT (75.8570 22.7190)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.99,
            "operating_hours": "Mon-Fri 08:00-16:00",
            "capacity": 1200,
            "current_load": 1100,
            "cap_status": "normal",
        },
        {
            "name": "Vijay Nagar Public School",
            "category_id": cat_map["education"],
            "area_id": neigh_map["Vijay Nagar"],
            "latitude": 22.7533,
            "longitude": 75.8937,
            "geometry": "POINT (75.8937 22.7533)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.94,
            "operating_hours": "Mon-Fri 08:30-15:30",
            "capacity": 800,
            "current_load": 780,
            "cap_status": "normal",
        },
        {
            "name": "DAVV University Campus School",
            "category_id": cat_map["education"],
            "area_id": neigh_map["Bhanwarkuan"],
            "latitude": 22.6896,
            "longitude": 75.8648,
            "geometry": "POINT (75.8648 22.6896)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.90,
            "operating_hours": "Mon-Fri 08:00-15:00",
            "capacity": 450,
            "current_load": 420,
            "cap_status": "normal",
        },
        # Transport
        {
            "name": "Indore Central Railway Station Transit Hub",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["Rajwada"],
            "latitude": 22.7175,
            "longitude": 75.8655,
            "geometry": "POINT (75.8655 22.7175)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.99,
            "operating_hours": "24/7 Operations",
            "capacity": 5000,
            "current_load": 3200,
            "cap_status": "normal",
        },
        {
            "name": "AICTSL Palasia iBus Station",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["Old Palasia"],
            "latitude": 22.7250,
            "longitude": 75.8845,
            "geometry": "POINT (75.8845 22.7250)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.96,
            "operating_hours": "05:30-23:30 Daily",
            "capacity": 2000,
            "current_load": 1500,
            "cap_status": "normal",
        },
        {
            "name": "Bhanwarkuan BRTS Bus Hub",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["Bhanwarkuan"],
            "latitude": 22.6880,
            "longitude": 75.8640,
            "geometry": "POINT (75.8640 22.6880)",
            "status": "temporarily_unavailable",  # Service condition variation!
            "verification_status": "verified",
            "confidence_score": 0.88,
            "operating_hours": "Out of Service due to corridor repair",
            "capacity": 800,
            "current_load": 0,
            "cap_status": "constrained",
        },
        # Water
        {
            "name": "Rajwada Municipal Water Supply",
            "category_id": cat_map["water"],
            "area_id": neigh_map["Rajwada"],
            "latitude": 22.7200,
            "longitude": 75.8560,
            "geometry": "POINT (75.8560 22.7200)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.97,
            "operating_hours": "Continuous supply",
            "capacity": 10000,
            "current_load": 7500,
            "cap_status": "normal",
        },
        {
            "name": "Narmada Phase-III Vijay Nagar Water Reservoir",
            "category_id": cat_map["water"],
            "area_id": neigh_map["Vijay Nagar"],
            "latitude": 22.7540,
            "longitude": 75.8950,
            "geometry": "POINT (75.8950 22.7540)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.89,
            "operating_hours": "06:00-20:00 Daily",
            "capacity": 2500,
            "current_load": 2400,
            "cap_status": "constrained",
        },
        {
            "name": "Bhanwarkuan Sector 4 Community Well",
            "category_id": cat_map["water"],
            "area_id": neigh_map["Bhanwarkuan"],
            "latitude": 22.6870,
            "longitude": 75.8630,
            "geometry": "POINT (75.8630 22.6870)",
            "status": "degraded",  # Service condition variation!
            "verification_status": "pending",
            "confidence_score": 0.72,
            "operating_hours": "Intermittent supply",
            "capacity": 1500,
            "current_load": 400,
            "cap_status": "constrained",
        },
        # Market
        {
            "name": "Rajwada Heritage Produce Market",
            "category_id": cat_map["market"],
            "area_id": neigh_map["Rajwada"],
            "latitude": 22.7185,
            "longitude": 75.8550,
            "geometry": "POINT (75.8550 22.7185)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.98,
            "operating_hours": "06:00-21:00 Daily",
            "capacity": 1500,
            "current_load": 1200,
            "cap_status": "normal",
        },
        {
            "name": "Chhappan Dukan Gourmet Market",
            "category_id": cat_map["market"],
            "area_id": neigh_map["Old Palasia"],
            "latitude": 22.7230,
            "longitude": 75.8810,
            "geometry": "POINT (75.8810 22.7230)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.93,
            "operating_hours": "Tue-Sun 07:00-19:00",
            "capacity": 700,
            "current_load": 550,
            "cap_status": "normal",
        },
    ]

    # Legacy service migration if upgrading from existing database
    legacy_service_map = {
        "Central Metro Hospital": "MY Hospital Indore",
        "West End Community Clinic": "Sarafa Community Dispensary",
        "Riverside Health Center": "Palasia Health Center",
        "Downtown Central Academy": "Rajwada Central School",
        "Highlands Public School": "Vijay Nagar Public School",
        "South Hillside Primary": "DAVV University Campus School",
        "Central Multimodal Transit Hub": "Indore Central Railway Station Transit Hub",
        "Riverside Metro Station": "AICTSL Palasia iBus Station",
        "South Hillside Bus Hub": "Bhanwarkuan BRTS Bus Hub",
        "Downtown Municipal Purification Facility": "Rajwada Municipal Water Supply",
        "Highlands Spring Water Point": "Narmada Phase-III Vijay Nagar Water Reservoir",
        "South Hillside Community Well #4": "Bhanwarkuan Sector 4 Community Well",
        "Grand Central Produce Market": "Rajwada Heritage Produce Market",
        "Riverside Farmers Market": "Chhappan Dukan Gourmet Market",
    }
    for old_sname, new_sname in legacy_service_map.items():
        old_srec = db.query(Service).filter_by(name=old_sname).first()
        if old_srec and not db.query(Service).filter_by(name=new_sname).first():
            old_srec.name = new_sname
            matching_sdata = next((s for s in services_data if s["name"] == new_sname), None)
            if matching_sdata:
                old_srec.latitude = matching_sdata["latitude"]
                old_srec.longitude = matching_sdata["longitude"]
                old_srec.geometry = matching_sdata["geometry"]
                old_srec.area_id = matching_sdata["area_id"]
            db.flush()

    service_map = {}
    for item in services_data:
        cap_val = item.pop("capacity")
        load_val = item.pop("current_load")
        cap_status = item.pop("cap_status")

        existing_svc = db.query(Service).filter_by(name=item["name"]).first()
        if not existing_svc:
            existing_svc = Service(**item, source_type="simulated_demo")
            db.add(existing_svc)
            db.flush()

            # Add Capacity
            cap = ServiceCapacity(
                service_id=existing_svc.id,
                capacity=cap_val,
                current_load=load_val,
                status=cap_status,
            )
            db.add(cap)
            db.flush()
        else:
            existing_svc.latitude = item["latitude"]
            existing_svc.longitude = item["longitude"]
            existing_svc.geometry = item["geometry"]
            existing_svc.area_id = item["area_id"]
            db.flush()

        service_map[existing_svc.name] = existing_svc.id

    # 6. COMMUNITY REPORTS & VERIFICATION (Real Indore civic reports)
    reports_data = [
        {
            "title": "Low water pressure and particulate matter in Sector 4 Well",
            "description": "Residents near Bhanwarkuan report brown water and severe drop in flow rate since yesterday.",
            "category_id": cat_map["water"],
            "service_id": service_map.get("Bhanwarkuan Sector 4 Community Well"),
            "area_id": neigh_map["Bhanwarkuan"],
            "latitude": 22.6872,
            "longitude": 75.8635,
            "geometry": "POINT (75.8635 22.6872)",
            "severity": "high",
            "status": "verified",
            "verification_status": "verified",
            "confidence_score": 0.95,
            "source_type": "simulated_demo",
            "verification": {
                "verifier_id": "auditor_demo_01",
                "verification_status": "verified",
                "verification_type": "official_audit",
                "notes": "Field technician confirmed pump filter clogging and sent water test for lab review.",
            },
        },
        {
            "title": "Bhanwarkuan BRTS Bus Hub closed due to corridor repairs",
            "description": "BRTS lane maintenance near Bhanwarkuan square, buses diverted along ring road.",
            "category_id": cat_map["transport"],
            "service_id": service_map.get("Bhanwarkuan BRTS Bus Hub"),
            "area_id": neigh_map["Bhanwarkuan"],
            "latitude": 22.6882,
            "longitude": 75.8642,
            "geometry": "POINT (75.8642 22.6882)",
            "severity": "critical",
            "status": "in_review",
            "verification_status": "pending",
            "confidence_score": 0.85,
            "source_type": "simulated_demo",
            "verification": {
                "verifier_id": "dispatch_agent_03",
                "verification_status": "pending",
                "verification_type": "peer_confirmation",
                "notes": "Traffic clearing team dispatched to verify corridor access clearance timeline.",
            },
        },
        {
            "title": "Severe clinic overcrowding and long triage delays",
            "description": "Over 50 patients waiting outside Palasia clinic. Triage nurse shortage reported.",
            "category_id": cat_map["healthcare"],
            "service_id": service_map.get("Palasia Health Center"),
            "area_id": neigh_map["Old Palasia"],
            "latitude": 22.7246,
            "longitude": 75.8841,
            "geometry": "POINT (75.8841 22.7246)",
            "severity": "medium",
            "status": "submitted",
            "verification_status": "unverified",
            "confidence_score": 0.70,
            "source_type": "simulated_demo",
            "verification": None,
        },
        {
            "title": "Urgent need for primary health centre in Vijay Nagar",
            "description": "Over 22,000 residents lack local basic clinic services; closest government hospital (MY Hospital) is over 25 minutes in traffic.",
            "category_id": cat_map["healthcare"],
            "service_id": None,
            "area_id": neigh_map["Vijay Nagar"],
            "latitude": 22.7535,
            "longitude": 75.8940,
            "geometry": "POINT (75.8940 22.7535)",
            "severity": "high",
            "status": "submitted",
            "verification_status": "unverified",
            "confidence_score": 0.80,
            "source_type": "simulated_demo",
            "verification": None,
        },
    ]

    for rep in reports_data:
        ver_info = rep.pop("verification")
        existing_rep = db.query(CommunityReport).filter_by(title=rep["title"]).first()
        if not existing_rep:
            existing_rep = CommunityReport(**rep)
            db.add(existing_rep)
            db.flush()

            if ver_info:
                ver = ReportVerification(
                    report_id=existing_rep.id,
                    **ver_info,
                )
                db.add(ver)
                db.flush()

    # 7. RBAC ROLES & PERMISSIONS
    permissions_data = [
        {"code": "data:read", "description": "Read public civic infrastructure and statistics"},
        {"code": "report:create", "description": "Submit citizen civic infrastructure reports"},
        {"code": "report:verify_community", "description": "Participate in community verification reviews"},
        {"code": "authority:operate", "description": "Execute urban planner and municipal operations"},
        {"code": "report:verify_official", "description": "Submit official municipal report verification"},
        {"code": "admin:manage", "description": "System administration, configuration, and user management"},
    ]

    for p_data in permissions_data:
        existing_p = db.query(Permission).filter_by(code=p_data["code"]).first()
        if not existing_p:
            db.add(Permission(**p_data))
    db.flush()

    perm_map = {p.code: p for p in db.query(Permission).all()}

    roles_data = [
        {
            "name": "citizen",
            "description": "General citizen with public data access and report creation",
            "perms": ["data:read", "report:create"],
        },
        {
            "name": "community",
            "description": "Community member with citizen capabilities and community verification rights",
            "perms": ["data:read", "report:create", "report:verify_community"],
        },
        {
            "name": "authority",
            "description": "Municipal planner and official authority with operations and verification privileges",
            "perms": ["data:read", "report:create", "report:verify_community", "report:verify_official", "authority:operate"],
        },
        {
            "name": "admin",
            "description": "System administrator with full administrative access",
            "perms": ["data:read", "report:create", "report:verify_community", "report:verify_official", "authority:operate", "admin:manage"],
        },
    ]

    for r_data in roles_data:
        existing_r = db.query(Role).filter_by(name=r_data["name"]).first()
        if not existing_r:
            role_obj = Role(name=r_data["name"], description=r_data["description"])
            role_obj.permissions = [perm_map[p_code] for p_code in r_data["perms"] if p_code in perm_map]
            db.add(role_obj)
        else:
            # Sync permissions
            role_obj = existing_r
            role_obj.permissions = [perm_map[p_code] for p_code in r_data["perms"] if p_code in perm_map]
    db.flush()

    role_map = {r.name: r for r in db.query(Role).all()}

    # 8. DEMO USERS (Deterministic credentials for testing)
    demo_users_data = [
        {
            "email": "citizen@example.com",
            "username": "citizen_demo",
            "password": "Citizen123!",
            "display_name": "Demo Citizen",
            "role_name": "citizen",
            "is_active": True,
        },
        {
            "email": "community@example.com",
            "username": "community_demo",
            "password": "Community123!",
            "display_name": "Demo Community Verifier",
            "role_name": "community",
            "is_active": True,
        },
        {
            "email": "authority@example.com",
            "username": "authority_demo",
            "password": "Authority123!",
            "display_name": "Demo Urban Planner",
            "role_name": "authority",
            "is_active": True,
        },
        {
            "email": "admin@example.com",
            "username": "admin_demo",
            "password": "Admin123!",
            "display_name": "Demo System Admin",
            "role_name": "admin",
            "is_active": True,
        },
        {
            "email": "inactive@example.com",
            "username": "inactive_demo",
            "password": "Inactive123!",
            "display_name": "Inactive Citizen",
            "role_name": "citizen",
            "is_active": False,
        },
    ]

    for u_data in demo_users_data:
        existing_u = db.query(User).filter_by(email=u_data["email"]).first()
        role_obj = role_map.get(u_data["role_name"])
        pwd_hash = hash_password(u_data["password"])

        if not existing_u:
            new_user = User(
                email=u_data["email"],
                username=u_data["username"],
                password_hash=pwd_hash,
                display_name=u_data["display_name"],
                role_id=role_obj.id,
                is_active=u_data["is_active"],
            )
            db.add(new_user)
        else:
            existing_u.password_hash = pwd_hash
            existing_u.role_id = role_obj.id
            existing_u.is_active = u_data["is_active"]
    db.flush()

    # 9. AUDIT LOG (Record seeding audit log)
    audit = AuditLog(
        actor_id="system_seed",
        action="seed",
        entity_type="database",
        entity_id=1,
        reason="Stage 2 auth and demo data generation",
        previous_value=None,
        new_value=json.dumps({
            "seeded_areas": len(neighbourhoods),
            "seeded_services": len(services_data),
            "seeded_roles": len(roles_data),
            "seeded_users": len(demo_users_data),
        }),
    )
    db.add(audit)

    db.commit()
    print("[SUCCESS] Deterministic demo data seeded successfully!")
    return {
        "data_sources": db.query(DataSource).count(),
        "categories": db.query(ServiceCategory).count(),
        "geographic_areas": db.query(GeographicArea).count(),
        "population_cells": db.query(PopulationCell).count(),
        "services": db.query(Service).count(),
        "service_capacities": db.query(ServiceCapacity).count(),
        "community_reports": db.query(CommunityReport).count(),
        "report_verifications": db.query(ReportVerification).count(),
        "roles": db.query(Role).count(),
        "permissions": db.query(Permission).count(),
        "users": db.query(User).count(),
        "audit_logs": db.query(AuditLog).count(),
    }


def main():
    db = SessionLocal()
    try:
        counts = seed_database(db)
        print("Seeded entity summary:")
        for entity, count in counts.items():
            print(f"  - {entity}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
