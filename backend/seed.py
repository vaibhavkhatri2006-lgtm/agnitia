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
from app.database import engine, SessionLocal
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
    # City root
    city = db.query(GeographicArea).filter_by(name="Metro City").first()
    if not city:
        city = GeographicArea(
            name="Metro City",
            area_type="city",
            parent_id=None,
            population=72000,
            geometry="MULTIPOLYGON (((77.5600 12.9400, 77.6400 12.9400, 77.6400 13.0100, 77.5600 13.0100, 77.5600 12.9400)))",
        )
        db.add(city)
        db.flush()

    # Districts
    districts = {
        "District 1 - Central Ward": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 37000,
            "geometry": "MULTIPOLYGON (((77.5800 12.9650, 77.6100 12.9650, 77.6100 12.9900, 77.5800 12.9900, 77.5800 12.9650)))",
        },
        "District 2 - Riverside North": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 18000,
            "geometry": "MULTIPOLYGON (((77.5850 12.9900, 77.6200 12.9900, 77.6200 13.0100, 77.5850 13.0100, 77.5850 12.9900)))",
        },
        "District 3 - Highlands East": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 22000,
            "geometry": "MULTIPOLYGON (((77.6100 12.9650, 77.6400 12.9650, 77.6400 12.9900, 77.6100 12.9900, 77.6100 12.9650)))",
        },
        "District 4 - Southern Outskirts": {
            "area_type": "ward",
            "parent_id": city.id,
            "population": 15000,
            "geometry": "MULTIPOLYGON (((77.5650 12.9400, 77.6000 12.9400, 77.6000 12.9650, 77.5650 12.9650, 77.5650 12.9400)))",
        },
    }

    dist_map = {}
    for name, data in districts.items():
        existing = db.query(GeographicArea).filter_by(name=name).first()
        if not existing:
            existing = GeographicArea(name=name, **data)
            db.add(existing)
            db.flush()
        dist_map[name] = existing.id

    # Neighbourhoods
    neighbourhoods = {
        "Downtown Core": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["District 1 - Central Ward"],
            "population": 25000,
            "geometry": "MULTIPOLYGON (((77.5850 12.9700, 77.6050 12.9700, 77.6050 12.9850, 77.5850 12.9850, 77.5850 12.9700)))",
        },
        "West End": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["District 1 - Central Ward"],
            "population": 12000,
            "geometry": "MULTIPOLYGON (((77.5800 12.9650, 77.5850 12.9650, 77.5850 12.9850, 77.5800 12.9850, 77.5800 12.9650)))",
        },
        "Riverside Commons": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["District 2 - Riverside North"],
            "population": 18000,
            "geometry": "MULTIPOLYGON (((77.5900 12.9900, 77.6150 12.9900, 77.6150 13.0080, 77.5900 13.0080, 77.5900 12.9900)))",
        },
        "Highlands Valley": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["District 3 - Highlands East"],
            "population": 22000,
            "geometry": "MULTIPOLYGON (((77.6120 12.9680, 77.6380 12.9680, 77.6380 12.9880, 77.6120 12.9880, 77.6120 12.9680)))",
        },
        "South Hillside": {
            "area_type": "neighbourhood",
            "parent_id": dist_map["District 4 - Southern Outskirts"],
            "population": 15000,
            "geometry": "MULTIPOLYGON (((77.5680 12.9420, 77.5980 12.9420, 77.5980 12.9630, 77.5680 12.9630, 77.5680 12.9420)))",
        },
    }

    neigh_map = {}
    for name, data in neighbourhoods.items():
        existing = db.query(GeographicArea).filter_by(name=name).first()
        if not existing:
            existing = GeographicArea(name=name, **data)
            db.add(existing)
            db.flush()
        neigh_map[name] = existing.id

    # 4. POPULATION CELLS (Fine-grained Demographic breakdown)
    cells_data = [
        {
            "area_id": neigh_map["Downtown Core"],
            "population": 15000,
            "geometry": "POLYGON ((77.5860 12.9710, 77.5950 12.9710, 77.5950 12.9800, 77.5860 12.9800, 77.5860 12.9710))",
            "demographics": json.dumps({"median_age": 32, "vulnerability_index": 0.20, "child_dependency": 0.15, "elderly_ratio": 0.10}),
        },
        {
            "area_id": neigh_map["Downtown Core"],
            "population": 10000,
            "geometry": "POLYGON ((77.5950 12.9710, 77.6040 12.9710, 77.6040 12.9800, 77.5950 12.9800, 77.5950 12.9710))",
            "demographics": json.dumps({"median_age": 34, "vulnerability_index": 0.22, "child_dependency": 0.18, "elderly_ratio": 0.11}),
        },
        {
            "area_id": neigh_map["Highlands Valley"],
            "population": 22000,
            "geometry": "POLYGON ((77.6150 12.9700, 77.6350 12.9700, 77.6350 12.9850, 77.6150 12.9850, 77.6150 12.9700))",
            "demographics": json.dumps({"median_age": 28, "vulnerability_index": 0.68, "child_dependency": 0.35, "elderly_ratio": 0.18}),
        },
        {
            "area_id": neigh_map["South Hillside"],
            "population": 15000,
            "geometry": "POLYGON ((77.5700 12.9450, 77.5950 12.9450, 77.5950 12.9600, 77.5700 12.9600, 77.5700 12.9450))",
            "demographics": json.dumps({"median_age": 31, "vulnerability_index": 0.74, "child_dependency": 0.38, "elderly_ratio": 0.21}),
        },
    ]

    for cell in cells_data:
        existing = db.query(PopulationCell).filter_by(area_id=cell["area_id"], population=cell["population"]).first()
        if not existing:
            db.add(PopulationCell(**cell, source_type="simulated_demo"))
    db.flush()

    # 5. SERVICES & CAPACITIES
    # Variation:
    # - Highlands Valley has NO clinic/hospital (poor healthcare access)
    # - South Hillside has bus point temporarily unavailable (poor transport access)
    # - Riverside health center is overloaded
    services_data = [
        # Healthcare
        {
            "name": "Central Metro Hospital",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["Downtown Core"],
            "latitude": 12.9750,
            "longitude": 77.5900,
            "geometry": "POINT (77.5900 12.9750)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.98,
            "operating_hours": "24/7 Emergency & Inpatient",
            "capacity": 500,
            "current_load": 380,
            "cap_status": "normal",
        },
        {
            "name": "West End Community Clinic",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["West End"],
            "latitude": 12.9720,
            "longitude": 77.5820,
            "geometry": "POINT (77.5820 12.9720)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.92,
            "operating_hours": "Mon-Sat 08:00-18:00",
            "capacity": 80,
            "current_load": 75,
            "cap_status": "constrained",
        },
        {
            "name": "Riverside Health Center",
            "category_id": cat_map["healthcare"],
            "area_id": neigh_map["Riverside Commons"],
            "latitude": 12.9980,
            "longitude": 77.6020,
            "geometry": "POINT (77.6020 12.9980)",
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
            "name": "Downtown Central Academy",
            "category_id": cat_map["education"],
            "area_id": neigh_map["Downtown Core"],
            "latitude": 12.9780,
            "longitude": 77.5960,
            "geometry": "POINT (77.5960 12.9780)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.99,
            "operating_hours": "Mon-Fri 08:00-16:00",
            "capacity": 1200,
            "current_load": 1100,
            "cap_status": "normal",
        },
        {
            "name": "Highlands Public School",
            "category_id": cat_map["education"],
            "area_id": neigh_map["Highlands Valley"],
            "latitude": 12.9760,
            "longitude": 77.6250,
            "geometry": "POINT (77.6250 12.9760)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.94,
            "operating_hours": "Mon-Fri 08:30-15:30",
            "capacity": 800,
            "current_load": 780,
            "cap_status": "normal",
        },
        {
            "name": "South Hillside Primary",
            "category_id": cat_map["education"],
            "area_id": neigh_map["South Hillside"],
            "latitude": 12.9520,
            "longitude": 77.5850,
            "geometry": "POINT (77.5850 12.9520)",
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
            "name": "Central Multimodal Transit Hub",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["Downtown Core"],
            "latitude": 12.9730,
            "longitude": 77.5920,
            "geometry": "POINT (77.5920 12.9730)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.99,
            "operating_hours": "24/7 Operations",
            "capacity": 5000,
            "current_load": 3200,
            "cap_status": "normal",
        },
        {
            "name": "Riverside Metro Station",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["Riverside Commons"],
            "latitude": 12.9950,
            "longitude": 77.6050,
            "geometry": "POINT (77.6050 12.9950)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.96,
            "operating_hours": "05:30-23:30 Daily",
            "capacity": 2000,
            "current_load": 1500,
            "cap_status": "normal",
        },
        {
            "name": "South Hillside Bus Hub",
            "category_id": cat_map["transport"],
            "area_id": neigh_map["South Hillside"],
            "latitude": 12.9500,
            "longitude": 77.5800,
            "geometry": "POINT (77.5800 12.9500)",
            "status": "temporarily_unavailable",  # Service condition variation!
            "verification_status": "verified",
            "confidence_score": 0.88,
            "operating_hours": "Out of Service due to landslide repair",
            "capacity": 800,
            "current_load": 0,
            "cap_status": "constrained",
        },
        # Water
        {
            "name": "Downtown Municipal Purification Facility",
            "category_id": cat_map["water"],
            "area_id": neigh_map["Downtown Core"],
            "latitude": 12.9790,
            "longitude": 77.5880,
            "geometry": "POINT (77.5880 12.9790)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.97,
            "operating_hours": "Continuous supply",
            "capacity": 10000,
            "current_load": 7500,
            "cap_status": "normal",
        },
        {
            "name": "Highlands Spring Water Point",
            "category_id": cat_map["water"],
            "area_id": neigh_map["Highlands Valley"],
            "latitude": 12.9740,
            "longitude": 77.6300,
            "geometry": "POINT (77.6300 12.9740)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.89,
            "operating_hours": "06:00-20:00 Daily",
            "capacity": 2500,
            "current_load": 2400,
            "cap_status": "constrained",
        },
        {
            "name": "South Hillside Community Well #4",
            "category_id": cat_map["water"],
            "area_id": neigh_map["South Hillside"],
            "latitude": 12.9480,
            "longitude": 77.5750,
            "geometry": "POINT (77.5750 12.9480)",
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
            "name": "Grand Central Produce Market",
            "category_id": cat_map["market"],
            "area_id": neigh_map["Downtown Core"],
            "latitude": 12.9725,
            "longitude": 77.5950,
            "geometry": "POINT (77.5950 12.9725)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.98,
            "operating_hours": "06:00-21:00 Daily",
            "capacity": 1500,
            "current_load": 1200,
            "cap_status": "normal",
        },
        {
            "name": "Riverside Farmers Market",
            "category_id": cat_map["market"],
            "area_id": neigh_map["Riverside Commons"],
            "latitude": 12.9920,
            "longitude": 77.6100,
            "geometry": "POINT (77.6100 12.9920)",
            "status": "operational",
            "verification_status": "verified",
            "confidence_score": 0.93,
            "operating_hours": "Tue-Sun 07:00-19:00",
            "capacity": 700,
            "current_load": 550,
            "cap_status": "normal",
        },
    ]

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

        service_map[existing_svc.name] = existing_svc.id

    # 6. COMMUNITY REPORTS & VERIFICATION (With variation in severity and status)
    reports_data = [
        {
            "title": "Low water pressure and particulate matter in Well #4",
            "description": "Residents in Sector 2 report brown water and severe drop in flow rate since yesterday.",
            "category_id": cat_map["water"],
            "service_id": service_map.get("South Hillside Community Well #4"),
            "area_id": neigh_map["South Hillside"],
            "latitude": 12.9482,
            "longitude": 77.5755,
            "geometry": "POINT (77.5755 12.9482)",
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
            "title": "South Hillside Bus Hub closed due to debris on feeder route",
            "description": "Feeder road blocked by fallen rocks, all feeder buses stranded or rerouted.",
            "category_id": cat_map["transport"],
            "service_id": service_map.get("South Hillside Bus Hub"),
            "area_id": neigh_map["South Hillside"],
            "latitude": 12.9502,
            "longitude": 77.5802,
            "geometry": "POINT (77.5802 12.9502)",
            "severity": "critical",
            "status": "in_review",
            "verification_status": "pending",
            "confidence_score": 0.85,
            "source_type": "simulated_demo",
            "verification": {
                "verifier_id": "dispatch_agent_03",
                "verification_status": "pending",
                "verification_type": "peer_confirmation",
                "notes": "Highway clearing team dispatched to verify access clearance timeline.",
            },
        },
        {
            "title": "Severe clinic overcrowding and long triage delays",
            "description": "Over 50 patients waiting outside in heat. Triage nurse shortage reported.",
            "category_id": cat_map["healthcare"],
            "service_id": service_map.get("Riverside Health Center"),
            "area_id": neigh_map["Riverside Commons"],
            "latitude": 12.9982,
            "longitude": 77.6022,
            "geometry": "POINT (77.6022 12.9982)",
            "severity": "medium",
            "status": "submitted",
            "verification_status": "unverified",
            "confidence_score": 0.70,
            "source_type": "simulated_demo",
            "verification": None,
        },
        {
            "title": "Urgent need for mobile medical clinic in Highlands Valley",
            "description": "Over 20,000 residents lack local basic clinic services; closest hospital is over 45 minutes by bus.",
            "category_id": cat_map["healthcare"],
            "service_id": None,
            "area_id": neigh_map["Highlands Valley"],
            "latitude": 12.9750,
            "longitude": 77.6280,
            "geometry": "POINT (77.6280 12.9750)",
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
