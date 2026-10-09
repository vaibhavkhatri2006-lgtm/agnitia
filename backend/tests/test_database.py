"""
CivicPulse Stage 1 Database & Model Tests
Covers:
- Model creation & required fields
- Foreign-key integrity & relationships
- Uniqueness constraints
- Geometry validity (via Shapely)
- Seed success & determinism
- Stage 1 Sample queries
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from shapely import wkt
from shapely.geometry.base import BaseGeometry

from app.database import Base
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
)
from seed import seed_database


@pytest.fixture(scope="module")
def db_session():
    """Provides a fresh isolated in-memory SQLite database session with all models created."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_seed_success_and_determinism(db_session):
    """Verify that seed runs cleanly and repeatedly produces deterministic results."""
    first_run = seed_database(db_session)
    assert first_run["categories"] == 5
    assert first_run["geographic_areas"] == 10
    assert first_run["services"] == 14
    assert first_run["service_capacities"] == 14
    assert first_run["community_reports"] == 4
    assert first_run["report_verifications"] == 2
    assert first_run["data_sources"] == 5

    # Run seed a second time to ensure strict determinism & idempotency
    second_run = seed_database(db_session)
    assert second_run["categories"] == 5
    assert second_run["geographic_areas"] == 10
    assert second_run["services"] == 14
    assert second_run["service_capacities"] == 14
    assert second_run["community_reports"] == 4
    assert second_run["report_verifications"] == 2


def test_model_creation_and_attributes(db_session):
    """Verify that models contain expected fields and default values."""
    ds = db_session.query(DataSource).filter_by(code="simulated_demo").first()
    assert ds is not None
    assert ds.trust_level == 0.70
    assert ds.is_active is True
    assert ds.created_at is not None

    cat = db_session.query(ServiceCategory).filter_by(code="healthcare").first()
    assert cat is not None
    assert cat.name == "Healthcare"
    assert cat.icon == "hospital"

    area = db_session.query(GeographicArea).filter_by(name="Downtown Core").first()
    assert area is not None
    assert area.area_type == "neighbourhood"
    assert area.population == 25000


def test_foreign_key_and_relationships(db_session):
    """Verify relationship traversal and foreign key integrity."""
    service = db_session.query(Service).filter_by(name="Central Metro Hospital").first()
    assert service is not None
    assert service.category.code == "healthcare"
    assert service.area.name == "Downtown Core"
    assert service.capacity_record is not None
    assert service.capacity_record.capacity == 500
    assert service.capacity_record.current_load == 380

    # Area hierarchy parent/children relationship
    downtown = db_session.query(GeographicArea).filter_by(name="Downtown Core").first()
    assert downtown.parent is not None
    assert downtown.parent.name == "District 1 - Central Ward"
    assert any(child.name == "Downtown Core" for child in downtown.parent.children)

    # Report verifications relationship
    report = db_session.query(CommunityReport).filter_by(severity="high").first()
    assert report is not None
    assert len(report.verifications) >= 1
    assert report.verifications[0].verification_status in ["verified", "pending"]


def test_uniqueness_constraints(db_session):
    """Verify unique constraints on categories, data sources, and 1-to-1 capacities."""
    # Duplicate category code
    dup_cat = ServiceCategory(code="healthcare", name="Duplicate Healthcare")
    db_session.add(dup_cat)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Duplicate data source code
    dup_ds = DataSource(code="osm", name="Duplicate OSM")
    db_session.add(dup_ds)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Duplicate service_capacity for the same service_id
    svc = db_session.query(Service).first()
    dup_cap = ServiceCapacity(service_id=svc.id, capacity=100)
    db_session.add(dup_cap)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_required_fields_and_integrity(db_session):
    """Verify that nullable=False columns reject None values."""
    # Service without name
    cat = db_session.query(ServiceCategory).first()
    invalid_svc = Service(
        name=None,
        category_id=cat.id,
        latitude=12.9,
        longitude=77.5,
        geometry="POINT (77.5 12.9)",
    )
    db_session.add(invalid_svc)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_geometry_validity(db_session):
    """Verify that all stored geometries are valid, non-empty, and within valid coordinate bounds."""
    # 1. Geographic Areas geometries
    areas = db_session.query(GeographicArea).all()
    assert len(areas) > 0
    for area in areas:
        if area.geometry:
            geom = wkt.loads(area.geometry)
            assert isinstance(geom, BaseGeometry)
            assert geom.is_valid, f"Invalid geometry in area {area.name}"
            assert not geom.is_empty
            minx, miny, maxx, maxy = geom.bounds
            assert -180 <= minx <= 180 and -180 <= maxx <= 180
            assert -90 <= miny <= 90 and -90 <= maxy <= 90

    # 2. Population Cells geometries
    cells = db_session.query(PopulationCell).all()
    assert len(cells) > 0
    for cell in cells:
        if cell.geometry:
            geom = wkt.loads(cell.geometry)
            assert geom.is_valid, f"Invalid geometry in cell id {cell.id}"
            assert not geom.is_empty
            assert geom.geom_type == "Polygon"

    # 3. Services geometries
    services = db_session.query(Service).all()
    assert len(services) > 0
    for svc in services:
        geom = wkt.loads(svc.geometry)
        assert geom.is_valid, f"Invalid geometry in service {svc.name}"
        assert not geom.is_empty
        assert geom.geom_type == "Point"
        assert -180 <= geom.x <= 180
        assert -90 <= geom.y <= 90

    # 4. Community Reports geometries
    reports = db_session.query(CommunityReport).all()
    assert len(reports) > 0
    for rep in reports:
        geom = wkt.loads(rep.geometry)
        assert geom.is_valid, f"Invalid geometry in report id {rep.id}"
        assert not geom.is_empty
        assert geom.geom_type == "Point"


def test_sample_queries(db_session):
    """Verify realistic sample queries across Stage 1 models."""
    # Query 1: Filter services by category code
    transport_services = (
        db_session.query(Service)
        .join(ServiceCategory)
        .filter(ServiceCategory.code == "transport")
        .all()
    )
    assert len(transport_services) == 3
    transit_names = [s.name for s in transport_services]
    assert "South Hillside Bus Hub" in transit_names

    # Query 2: Find services with constrained or overloaded capacity
    stressed_services = (
        db_session.query(Service)
        .join(ServiceCapacity)
        .filter(ServiceCapacity.status.in_(["constrained", "overloaded"]))
        .all()
    )
    assert len(stressed_services) >= 3

    # Query 3: Identify underserved areas (e.g. neighbourhoods lacking healthcare)
    healthcare_cat = db_session.query(ServiceCategory).filter_by(code="healthcare").first()
    neighbourhoods = (
        db_session.query(GeographicArea)
        .filter(GeographicArea.area_type == "neighbourhood")
        .all()
    )
    underserved_neighbourhoods = []
    for neigh in neighbourhoods:
        has_hc = any(s.category_id == healthcare_cat.id for s in neigh.services)
        if not has_hc:
            underserved_neighbourhoods.append(neigh.name)

    # Highlands Valley and South Hillside should naturally lack direct clinics
    assert "Highlands Valley" in underserved_neighbourhoods
    assert "South Hillside" in underserved_neighbourhoods

    # Query 4: Find critical community reports
    critical_reports = (
        db_session.query(CommunityReport)
        .filter(CommunityReport.severity == "critical")
        .all()
    )
    assert len(critical_reports) == 1
    assert "Bus Hub" in critical_reports[0].title

    # Query 5: Population aggregation across districts
    city = db_session.query(GeographicArea).filter_by(area_type="city").first()
    total_ward_pop = sum(child.population for child in city.children if child.area_type == "ward")
    assert total_ward_pop == 92000
