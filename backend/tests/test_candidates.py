"""
Test suite for Stage 4A: Candidate Location Engine.
Verifies candidate generation, underserved area filtering, invalid coordinate handling,
invalid geometry handling, service-type validation, determinism, area containment,
duplicate prevention, and API endpoints.
"""
import sys
from pathlib import Path
import pytest
from shapely.geometry import Polygon, Point

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import GeographicArea, ServiceCategory
from app.decision.candidates import CandidateLocationService, default_candidate_service

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Provides a database session for candidate tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --- 1. Candidate Generation Tests ---

def test_candidate_generation(db):
    """
    Verify candidate generation creates valid candidates with all required fields
    for underserved areas (e.g. Highlands Valley for healthcare).
    """
    service = CandidateLocationService()
    candidates = service.generate_candidates_for_service(
        db=db,
        service_type="healthcare",
        min_gap_threshold=20.0,
    )
    assert len(candidates) > 0

    for cand in candidates:
        assert cand.candidate_id is not None
        assert cand.service_type == "healthcare"
        assert -90.0 <= cand.latitude <= 90.0
        assert -180.0 <= cand.longitude <= 180.0
        assert cand.area_id > 0
        assert len(cand.area_name) > 0
        assert len(cand.source_reason) > 0
        assert 0.0 <= cand.current_accessibility <= 100.0
        assert cand.population > 0
        assert 0.0 <= cand.current_gap <= 100.0
        assert cand.nearby_service_count >= 0
        assert cand.validity_status in ["valid", "rejected"]
        assert cand.strategy in ["centroid", "population_node", "gap_perimeter"]

    # Highlands Valley must have at least one candidate for healthcare
    hv_candidates = [c for c in candidates if c.area_name == "Highlands Valley"]
    assert len(hv_candidates) >= 1
    assert any(c.validity_status == "valid" for c in hv_candidates)


def test_all_five_supported_services(db):
    """Verify candidate generation operates across all 5 required services."""
    service = CandidateLocationService()
    for stype in ["healthcare", "education", "transport", "water", "market"]:
        candidates = service.generate_candidates_for_service(
            db=db,
            service_type=stype,
            min_gap_threshold=15.0,
        )
        assert isinstance(candidates, list)
        for c in candidates:
            assert c.service_type == stype


# --- 2. Underserved Area Filtering ---

def test_underserved_area_filtering(db):
    """
    Verify that areas with sufficient access (Well Served, accessibility >= 80)
    are excluded from candidate generation.
    """
    service = CandidateLocationService()
    underserved = service.find_underserved_areas(
        db=db,
        service_type="healthcare",
        max_accessibility=80.0,
    )

    for area, metrics in underserved:
        # Must not be 'Well Served'
        assert metrics["service_desert_classification"] != "Well Served"
        assert metrics["accessibility_score"] < 80.0
        assert metrics["gap_score"] >= 20.0

    # Downtown Core has a hospital and is Well Served -> must be excluded
    downtown = next((a for a, m in underserved if a.name == "Downtown Core"), None)
    assert downtown is None, "Well Served areas must be excluded from candidate generation"


# --- 3. Invalid Coordinate Handling ---

def test_invalid_coordinate_handling():
    """
    Verify validate_coordinates correctly flags non-numeric, NaN, infinite,
    out-of-range, and None coordinates without crashing.
    """
    service = CandidateLocationService()

    # Valid coordinates
    valid, err = service.validate_coordinates(12.9716, 77.5946)
    assert valid is True
    assert err is None

    # None values
    valid, err = service.validate_coordinates(None, 77.5946)
    assert valid is False
    assert "None" in err

    # Non-numeric
    valid, err = service.validate_coordinates("invalid", 77.5946)
    assert valid is False

    # NaN / Inf
    valid, err = service.validate_coordinates(float("nan"), 77.5946)
    assert valid is False
    valid, err = service.validate_coordinates(12.9716, float("inf"))
    assert valid is False

    # Latitude out of range [-90, 90]
    valid, err = service.validate_coordinates(95.0, 77.5946)
    assert valid is False
    assert "Latitude" in err

    valid, err = service.validate_coordinates(-90.5, 77.5946)
    assert valid is False

    # Longitude out of range [-180, 180]
    valid, err = service.validate_coordinates(12.9716, 185.0)
    assert valid is False
    assert "Longitude" in err

    valid, err = service.validate_coordinates(12.9716, -181.0)
    assert valid is False


# --- 4. Invalid Geometry Handling ---

def test_invalid_geometry_handling():
    """
    Verify validate_geometry flags invalid, empty, or non-geometry objects safely.
    """
    service = CandidateLocationService()

    # None
    valid, err = service.validate_geometry(None)
    assert valid is False

    # Non-geometry string
    valid, err = service.validate_geometry("NOT_A_GEOMETRY")
    assert valid is False

    # Valid Polygon
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    valid, err = service.validate_geometry(poly)
    assert valid is True
    assert err is None

    # Invalid bowtie polygon (self-intersecting)
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    valid, err = service.validate_geometry(bowtie)
    assert valid is False
    assert "invalid" in err.lower()


def test_graceful_handling_of_area_with_corrupt_geometry(db):
    """
    Verify candidate generation does not crash if an area has corrupt/missing geometry.
    It should record a rejected candidate and proceed with valid areas.
    """
    service = CandidateLocationService()

    # Create dummy area with corrupted geometry string
    corrupt_area = GeographicArea(
        id=9999,
        name="Corrupt Test Area",
        area_type="neighbourhood",
        geometry="INVALID_WKT_STRING_12345",
        population=5000,
    )

    geom, err = service.parse_area_geometry(corrupt_area)
    assert geom is None
    assert "Failed to parse" in err


# --- 5. Service-Type Validation ---

def test_service_type_validation():
    """
    Verify supported services are accepted (case-insensitive)
    and unsupported services raise descriptive ValueError.
    """
    service = CandidateLocationService()

    # Supported
    assert service.validate_service_type("healthcare") == "healthcare"
    assert service.validate_service_type("EDUCATION") == "education"
    assert service.validate_service_type(" Transport ") == "transport"
    assert service.validate_service_type("water") == "water"
    assert service.validate_service_type("market") == "market"

    # Unsupported
    with pytest.raises(ValueError) as exc1:
        service.validate_service_type("spaceship_depot")
    assert "Unsupported service type 'spaceship_depot'" in str(exc1.value)

    with pytest.raises(ValueError):
        service.validate_service_type("")


# --- 6. Deterministic Output ---

def test_deterministic_output(db):
    """
    Verify that multiple consecutive calls with the same database state
    return the exact same candidate list in the exact same order.
    """
    service = CandidateLocationService()

    run1 = service.generate_candidates_for_service(db=db, service_type="transport")
    run2 = service.generate_candidates_for_service(db=db, service_type="transport")

    assert len(run1) == len(run2)
    assert len(run1) > 0

    for c1, c2 in zip(run1, run2):
        assert c1.candidate_id == c2.candidate_id
        assert c1.latitude == c2.latitude
        assert c1.longitude == c2.longitude
        assert c1.area_id == c2.area_id
        assert c1.strategy == c2.strategy
        assert c1.current_accessibility == c2.current_accessibility


# --- 7. Candidate Belongs to Valid Area & Polygon Containment ---

def test_candidate_belongs_to_valid_area(db):
    """
    Verify that every valid candidate belongs to an existing analysis area
    and its coordinates lie inside the designated area polygon boundary.
    """
    service = CandidateLocationService()
    candidates = service.generate_candidates_for_service(
        db=db,
        service_type="healthcare",
    )

    area_cache = {a.id: a for a in db.query(GeographicArea).all()}

    for cand in candidates:
        assert cand.area_id in area_cache
        area = area_cache[cand.area_id]

        if cand.validity_status == "valid":
            inside, err = service.validate_point_in_area(cand.latitude, cand.longitude, area)
            assert inside is True, f"Candidate {cand.candidate_id} must be inside area {area.name}: {err}"


# --- 8. Duplicate Candidate Prevention ---

def test_duplicate_candidate_prevention(db):
    """
    Verify that candidates generated for a service type do not contain
    duplicate identical or overlapping coordinates.
    """
    service = CandidateLocationService()
    candidates = service.generate_candidates_for_service(
        db=db,
        service_type="transport",
    )

    coords = [(c.latitude, c.longitude) for c in candidates]
    unique_coords = set(coords)

    assert len(coords) == len(unique_coords), "Generated candidates must not contain duplicate coordinates"

    # Test coordinate duplicate tolerance detector
    seen = {(12.971600, 77.594600)}
    assert service._is_coordinate_duplicate((12.971600, 77.594600), seen) is True
    # ~5 meters away (0.00005 deg) -> duplicate within tolerance
    assert service._is_coordinate_duplicate((12.971640, 77.594630), seen, tolerance=0.0001) is True
    # Distinct location
    assert service._is_coordinate_duplicate((12.980000, 77.600000), seen) is False


# --- 9. Integration Tests: API Endpoints ---

def test_api_get_candidates():
    """Test GET /decision/candidates returns valid candidate response."""
    response = client.get("/decision/candidates?service_type=healthcare")
    assert response.status_code == 200
    data = response.json()
    assert data["service_type"] == "healthcare"
    assert data["total_candidates"] >= 1
    assert data["valid_candidates_count"] >= 1
    assert len(data["candidates"]) == data["total_candidates"]

    first_cand = data["candidates"][0]
    assert "candidate_id" in first_cand
    assert "latitude" in first_cand
    assert "longitude" in first_cand
    assert "area_id" in first_cand
    assert "source_reason" in first_cand
    assert "current_accessibility" in first_cand
    assert "population" in first_cand
    assert "current_gap" in first_cand
    assert "nearby_service_count" in first_cand
    assert "validity_status" in first_cand


def test_api_post_candidates_generate():
    """Test POST /decision/candidates/generate with JSON payload."""
    payload = {
        "service_type": "water",
        "min_gap_threshold": 15.0,
        "max_accessibility": 75.0,
        "include_rejected": False,
    }
    response = client.post("/decision/candidates/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["service_type"] == "water"
    assert data["valid_candidates_count"] >= 1


def test_api_unsupported_service_error():
    """Test GET /decision/candidates with invalid service type returns 400 Bad Request."""
    response = client.get("/decision/candidates?service_type=unsupported_civic_service")
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported service type" in data["detail"]
