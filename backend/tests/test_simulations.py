"""
Unit and Integration Tests for What-If / Intervention Simulation Engine (Stage 4C).
Verifies before/after state calculations, impact metrics, deterministic outputs,
input validations, and strict database integrity (no permanent writes).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import (
    Service,
    ServiceCapacity,
    GeographicArea,
    ServiceCategory,
    PopulationCell,
    CommunityReport,
)
from app.decision.simulation import default_simulation_service, InterventionSimulationService


@pytest.fixture(scope="module")
def client():
    """Reusable TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 1. Valid Simulation Test ---
def test_valid_simulation_with_candidate(client):
    """Verifies that a valid simulation request with candidate_id succeeds with all required fields."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
            "proposed_capacity": 5000,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["simulation_id"].startswith("sim-healthcare-")
    assert data["service_type"] == "healthcare"
    assert data["candidate_id"] == "cand-healthcare-9-centroid"
    assert "before" in data
    assert "after" in data
    assert "impact" in data
    assert "target_area" in data
    assert "explanation" in data
    assert "primary_factors" in data
    assert data["confidence"] > 0.0

    # Target area checks
    assert data["target_area"]["area_name"] == "Highlands Valley"
    assert data["target_area"]["before_classification"] == "Critical Desert"
    assert data["target_area"]["after_classification"] == "Adequate"
    assert data["target_area"]["accessibility_improvement"] > 50.0


def test_valid_simulation_with_coordinates(client):
    """Verifies that a valid simulation request with latitude and longitude succeeds."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "latitude": 12.984123,
            "longitude": 77.632145,
            "scope": "city",
            "proposed_name": "New Highlands Clinic",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["candidate_id"] is None
    assert round(data["latitude"], 4) == 12.9841
    assert round(data["longitude"], 4) == 77.6321
    assert data["target_area"]["area_name"] == "Highlands Valley"
    assert data["impact"]["coverage_improvement"] > 0.0


# --- 2. Invalid Service Type Test ---
def test_invalid_service_type(client):
    """Verifies that unsupported service types are rejected with 400 Bad Request."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "spaceship_dock",
            "candidate_id": "cand-healthcare-9-centroid",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported service type" in data["detail"]
    assert "healthcare" in data["detail"]


# --- 3. Invalid Coordinates Test ---
def test_invalid_coordinates(client):
    """Verifies that out-of-bounds or non-numeric coordinates are rejected."""
    # Out of latitude bounds
    r1 = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "latitude": 999.0,
            "longitude": 77.63,
        },
    )
    assert r1.status_code in [400, 422]

    # Out of longitude bounds
    r2 = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "latitude": 12.98,
            "longitude": -500.0,
        },
    )
    assert r2.status_code in [400, 422]

    # Service-level coordinate validator test
    with pytest.raises(ValueError, match="out of valid bounds"):
        default_simulation_service.validate_coordinates(95.0, 77.0)

    with pytest.raises(ValueError, match="out of valid bounds"):
        default_simulation_service.validate_coordinates(12.0, -190.0)

    with pytest.raises(ValueError, match="valid numeric"):
        default_simulation_service.validate_coordinates("invalid", 77.0)


# --- 4. Invalid Candidate Test ---
def test_invalid_candidate(client):
    """Verifies that non-existent or invalid candidate IDs are rejected with 400 Bad Request."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-nonexistent-999-centroid",
        },
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()

    # Neither candidate nor coordinates provided
    resp_empty = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
        },
    )
    assert resp_empty.status_code == 400
    assert "either 'candidate_id' or both 'latitude' and 'longitude'" in resp_empty.json()["detail"].lower()


# --- 5. Before/After Calculation Consistency Test ---
def test_before_after_calculation(client):
    """Verifies mathematical consistency between before and after states."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()

    before = data["before"]
    after = data["after"]
    impact = data["impact"]

    # Before metrics validity
    assert 0.0 <= before["accessibility_score"] <= 100.0
    assert 0.0 <= before["gap_score"] <= 100.0
    assert 0.0 <= before["service_coverage"] <= 100.0
    assert before["underserved_population"] >= 0
    assert before["average_travel_time_minutes"] > 0.0

    # After metrics validity
    assert 0.0 <= after["accessibility_score"] <= 100.0
    assert 0.0 <= after["gap_score"] <= 100.0
    assert 0.0 <= after["service_coverage"] <= 100.0
    assert after["underserved_population"] >= 0
    assert after["average_travel_time_minutes"] >= 0.0

    # Mathematical delta consistency
    assert after["accessibility_score"] >= before["accessibility_score"]
    assert after["gap_score"] <= before["gap_score"]
    assert after["service_coverage"] >= before["service_coverage"]
    assert after["underserved_population"] <= before["underserved_population"]

    # Impact calculation exact match
    expected_access_imp = round(after["accessibility_score"] - before["accessibility_score"], 1)
    assert abs(impact["accessibility_improvement"] - expected_access_imp) <= 0.1

    expected_gap_red = round(before["gap_score"] - after["gap_score"], 1)
    assert abs(impact["gap_reduction"] - expected_gap_red) <= 0.1


# --- 6. Coverage Improvement Test ---
def test_coverage_improvement(client):
    """Verifies that placing a facility in an underserved area improves coverage percentage."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Highlands Valley has 22,000 / 92,000 = ~23.9% of total neighbourhood population
    assert data["before"]["service_coverage"] == 76.1
    assert data["after"]["service_coverage"] == 100.0
    assert data["impact"]["coverage_improvement"] == 23.9


# --- 7. Underserved Population Change Test ---
def test_underserved_population_change(client):
    """Verifies that underserved population decreases by the exact population of the newly served community."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["before"]["underserved_population"] == 22000
    assert data["after"]["underserved_population"] == 0
    assert data["impact"]["underserved_population_reduction"] == 22000
    assert data["impact"]["population_gaining_access"] == 22000


# --- 8. Travel Time Improvement Test ---
def test_travel_time_improvement(client):
    """Verifies that average travel time improves and travel time saved is properly reported."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["impact"]["travel_time_improvement_minutes"] > 0.0
    assert data["after"]["average_travel_time_minutes"] < data["before"]["average_travel_time_minutes"]
    assert data["target_area"]["travel_time_saved_minutes"] > 30.0


# --- 9. Deterministic Results Test ---
def test_deterministic_results(client):
    """Verifies that identical simulation inputs produce identical deterministic outputs."""
    payload = {
        "service_type": "water",
        "candidate_id": "cand-water-8-centroid",
        "scope": "city",
    }
    r1 = client.post("/simulations", json=payload)
    r2 = client.post("/simulations", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200

    d1 = r1.json()
    d2 = r2.json()

    assert d1["simulation_id"] == d2["simulation_id"]
    assert d1["before"] == d2["before"]
    assert d1["after"] == d2["after"]
    assert d1["impact"] == d2["impact"]
    assert d1["explanation"] == d2["explanation"]
    assert d1["primary_factors"] == d2["primary_factors"]


# --- 10. Database Integrity Test (NO PERMANENT MODIFICATIONS) ---
def test_no_permanent_database_modification(client, db_session):
    """
    CRITICAL SAFETY REQUIREMENT:
    Verifies that running a simulation does NOT insert or modify database records.
    All official counts and records must remain strictly identical.
    """
    count_services_before = db_session.query(Service).count()
    count_capacities_before = db_session.query(ServiceCapacity).count()
    count_areas_before = db_session.query(GeographicArea).count()
    count_pop_before = db_session.query(PopulationCell).count()
    count_reports_before = db_session.query(CommunityReport).count()

    # Run simulation multiple times with different services and parameters
    r1 = client.post(
        "/simulations",
        json={"service_type": "healthcare", "candidate_id": "cand-healthcare-9-centroid"},
    )
    assert r1.status_code == 200

    r2 = client.post(
        "/simulations",
        json={"service_type": "water", "latitude": 12.985, "longitude": 77.615},
    )
    assert r2.status_code == 200

    r3 = client.post(
        "/simulations",
        json={"service_type": "transport", "candidate_id": "cand-transport-9-centroid"},
    )
    assert r3.status_code == 200

    # Re-verify counts
    assert db_session.query(Service).count() == count_services_before
    assert db_session.query(ServiceCapacity).count() == count_capacities_before
    assert db_session.query(GeographicArea).count() == count_areas_before
    assert db_session.query(PopulationCell).count() == count_pop_before
    assert db_session.query(CommunityReport).count() == count_reports_before

    # Explicitly verify no simulated service exists in DB
    assert db_session.query(Service).filter_by(source_type="simulation").count() == 0
    assert db_session.query(Service).filter(Service.id < 0).count() == 0


# --- 11. Explanation Fields Test ---
def test_explanation_fields(client):
    """Verifies that explanation text and primary factors are well-formed and descriptive."""
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
        },
    )
    assert response.status_code == 200
    data = response.json()

    explanation = data["explanation"]
    factors = data["primary_factors"]

    assert isinstance(explanation, str)
    assert len(explanation) > 30
    assert "Highlands Valley" in explanation
    assert "healthcare" in explanation

    assert isinstance(factors, list)
    assert len(factors) > 0
    for expected in ["travel_time_reduction", "service_desert_resolution", "capacity_addition"]:
        assert expected in factors


# --- 12. Negative/Invalid Impact Protection Test ---
def test_negative_invalid_impact_protection(client):
    """
    Verifies that simulating an intervention in an already saturated/well-served area
    never returns negative impact values or invalid calculations.
    """
    # Downtown Core centroid (already has high accessibility 82.8)
    response = client.post(
        "/simulations",
        json={
            "service_type": "healthcare",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()
    impact = data["impact"]

    assert impact["accessibility_improvement"] >= 0.0
    assert impact["gap_reduction"] >= 0.0
    assert impact["coverage_improvement"] >= 0.0
    assert impact["underserved_population_reduction"] >= 0
    assert impact["population_gaining_access"] >= 0
    assert impact["travel_time_improvement_minutes"] >= 0.0


# --- 13. Scope Options Test ---
def test_scope_options(client):
    """Verifies that simulation handles different scope options: city, specific area ID, target area."""
    # City scope
    r_city = client.post(
        "/simulations",
        json={"service_type": "healthcare", "candidate_id": "cand-healthcare-9-centroid", "scope": "city"},
    )
    assert r_city.status_code == 200
    assert r_city.json()["scope"] == "city"

    # Specific area scope
    r_area = client.post(
        "/simulations",
        json={"service_type": "healthcare", "candidate_id": "cand-healthcare-9-centroid", "scope": "9"},
    )
    assert r_area.status_code == 200
    assert r_area.json()["scope"] == "area_9"
    assert r_area.json()["before"]["accessibility_score"] == 13.1
    assert r_area.json()["after"]["accessibility_score"] == 78.8

    # Target area scope
    r_target = client.post(
        "/simulations",
        json={"service_type": "healthcare", "candidate_id": "cand-healthcare-9-centroid", "scope": "target_area"},
    )
    assert r_target.status_code == 200
    assert r_target.json()["scope"] == "area_9"


# --- 14. GET /simulations Query-Param Test ---
def test_get_simulations_endpoint(client):
    """Verifies that GET /simulations functions identically with query parameters."""
    response = client.get(
        "/simulations",
        params={
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["service_type"] == "healthcare"
    assert data["target_area"]["area_name"] == "Highlands Valley"


# --- 15. All Supported Service Types Test ---
def test_all_supported_service_types(client):
    """Verifies that simulation works deterministically for all 5 supported civic service types."""
    services = ["healthcare", "education", "transport", "water", "market"]
    for svc in services:
        response = client.post(
            "/simulations",
            json={
                "service_type": svc,
                "latitude": 12.984123,
                "longitude": 77.632145,
            },
        )
        assert response.status_code == 200, f"Simulation failed for service {svc}: {response.text}"
        data = response.json()
        assert data["service_type"] == svc
        assert data["target_area"] is not None
        assert "before" in data
        assert "after" in data
        assert "impact" in data
