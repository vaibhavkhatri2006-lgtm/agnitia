"""
Tests for Stage 9: Scenario Lab + Investment + Resilience.
Validates the 7 required checks:
1. Add-service simulation returns valid before/after metrics.
2. Scenario comparison returns consistent results.
3. Investment ranking is deterministic.
4. Facility failure produces valid impact metrics.
5. Invalid inputs are rejected.
6. Simulation does not permanently modify official data.
7. Relevant Stage 4 and Stage 8 regression tests pass.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import Service, GeographicArea, CommunityReport


@pytest.fixture(scope="module")
def client():
    """Reusable TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Provides a database session for database consistency verification."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Check 1: Add-service simulation returns valid before/after metrics ---
def test_add_service_simulation_metrics(client):
    """
    Simulate adding a service at a candidate location.
    Verify before/after accessibility, coverage, underserved population, and travel-time metrics.
    """
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

    assert data["simulation_id"].startswith("sim-healthcare-")
    assert data["service_type"] == "healthcare"
    assert data["candidate_id"] == "cand-healthcare-9-centroid"
    assert data["confidence"] > 0.0

    # Validate before state metrics
    before = data["before"]
    assert "accessibility_score" in before
    assert "gap_score" in before
    assert "service_coverage" in before
    assert "underserved_population" in before
    assert "average_travel_time_minutes" in before
    assert 0.0 <= before["accessibility_score"] <= 100.0

    # Validate after state metrics
    after = data["after"]
    assert "accessibility_score" in after
    assert "gap_score" in after
    assert "service_coverage" in after
    assert "underserved_population" in after
    assert "average_travel_time_minutes" in after
    assert 0.0 <= after["accessibility_score"] <= 100.0

    # Validate impact deltas
    impact = data["impact"]
    assert impact["accessibility_improvement"] >= 0.0
    assert impact["gap_reduction"] >= 0.0
    assert impact["coverage_improvement"] >= 0.0
    assert impact["underserved_population_reduction"] >= 0
    assert impact["travel_time_improvement_minutes"] >= 0.0


# --- Check 2: Scenario comparison returns consistent results ---
def test_scenario_comparison_auto(client):
    """
    Compares baseline current state, 1 new facility, and 2 new facilities.
    Ensures consistent metrics across all scenarios.
    """
    for endpoint in ["/simulations/scenarios", "/decision/scenarios"]:
        response = client.get(f"{endpoint}?service_type=healthcare&scope=city")
        assert response.status_code == 200
        data = response.json()

        assert data["service_type"] == "healthcare"
        assert data["is_simulated"] is True
        assert "baseline" in data
        assert "scenarios" in data
        assert len(data["scenarios"]) >= 2

        # Check baseline scenario
        baseline = data["baseline"]
        assert baseline["scenario_id"] == "baseline"
        assert baseline["facilities_added"] == 0
        b_metrics = baseline["metrics"]
        assert "accessibility_score" in b_metrics
        assert "gap_score" in b_metrics
        assert "service_coverage" in b_metrics
        assert "underserved_population" in b_metrics
        assert "average_travel_time_minutes" in b_metrics

        # Check single facility vs multiple facilities consistency
        single_sc = next((s for s in data["scenarios"] if s["facilities_added"] == 1), None)
        multi_sc = next((s for s in data["scenarios"] if s["facilities_added"] == 2), None)

        if single_sc:
            assert single_sc["impact_vs_baseline"]["accessibility_improvement"] >= 0.0
            assert single_sc["metrics"]["accessibility_score"] >= b_metrics["accessibility_score"]

        if single_sc and multi_sc:
            # Monotonicity: 2 facilities should yield >= accessibility improvement compared to 1
            assert (
                multi_sc["impact_vs_baseline"]["accessibility_improvement"]
                >= single_sc["impact_vs_baseline"]["accessibility_improvement"]
            )
            assert (
                multi_sc["metrics"]["accessibility_score"]
                >= single_sc["metrics"]["accessibility_score"]
            )


def test_scenario_comparison_custom_post(client):
    """
    Compares custom user-defined multi-facility scenarios via POST.
    """
    payload = {
        "service_type": "education",
        "scope": "city",
        "scenarios": [
            {
                "scenario_id": "plan_alpha",
                "name": "Alpha School",
                "description": "Construct single school in underserved area",
                "facilities": [
                    {
                        "latitude": 12.9800,
                        "longitude": 77.6000,
                        "proposed_capacity": 3000,
                        "proposed_name": "East Primary School",
                    }
                ],
            },
            {
                "scenario_id": "plan_beta",
                "name": "Beta Multi-Campus",
                "description": "Construct two schools in north and south quadrants",
                "facilities": [
                    {
                        "latitude": 12.9800,
                        "longitude": 77.6000,
                        "proposed_capacity": 3000,
                        "proposed_name": "East Primary School",
                    },
                    {
                        "latitude": 12.9500,
                        "longitude": 77.5800,
                        "proposed_capacity": 4000,
                        "proposed_name": "South Campus High School",
                    },
                ],
            },
        ],
    }

    response = client.post("/simulations/scenarios", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["service_type"] == "education"
    sc_list = data["scenarios"]
    assert len(sc_list) == 3  # baseline + plan_alpha + plan_beta

    alpha = next(s for s in sc_list if s["scenario_id"] == "plan_alpha")
    beta = next(s for s in sc_list if s["scenario_id"] == "plan_beta")

    assert alpha["facilities_added"] == 1
    assert beta["facilities_added"] == 2
    assert "metrics" in alpha and "metrics" in beta
    assert beta["metrics"]["accessibility_score"] >= alpha["metrics"]["accessibility_score"]


# --- Check 3: Investment ranking is deterministic ---
def test_investment_ranking_deterministic(client):
    """
    Verifies that calling investment priority ranking repeatedly produces identical
    scores, ranks, and rationales.
    """
    res1 = client.get("/decision/investment-priorities?service_type=healthcare&max_results=5")
    assert res1.status_code == 200
    data1 = res1.json()

    res2 = client.post(
        "/decision/investment-priorities",
        json={"service_type": "healthcare", "max_results": 5},
    )
    assert res2.status_code == 200
    data2 = res2.json()

    # Compare results
    ranked1 = data1["ranked_investments"]
    ranked2 = data2["ranked_investments"]
    assert len(ranked1) == len(ranked2)
    assert len(ranked1) > 0

    for item1, item2 in zip(ranked1, ranked2):
        assert item1["rank"] == item2["rank"]
        assert item1["candidate_id"] == item2["candidate_id"]
        assert item1["investment_priority_score"] == pytest.approx(item2["investment_priority_score"])
        assert item1["expected_impact_score"] == pytest.approx(item2["expected_impact_score"])
        assert item1["population_affected"] == item2["population_affected"]
        assert item1["priority_tier"] == item2["priority_tier"]
        assert item1["rationale"] == item2["rationale"]


# --- Check 4: Facility failure produces valid impact metrics ---
def test_facility_failure_simulation(client, db_session):
    """
    Simulates a facility outage and validates affected population and accessibility drop.
    """
    # Pick an existing service
    svc = db_session.query(Service).filter_by(status="operational").first()
    assert svc is not None

    response = client.post(
        "/decision/failure-simulation",
        json={
            "service_id": svc.id,
            "failure_scenario_name": f"Planned maintenance outage of {svc.name}",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["service_id"] == svc.id
    assert data["service_name"] == svc.name
    assert data["directly_affected_population"] >= 0
    assert data["accessibility_drop"] >= 0.0
    assert data["coverage_loss"] >= 0.0
    assert 0.0 <= data["resilience_score"] <= 100.0
    assert "criticality_tier" in data
    assert isinstance(data["explanation"], str)
    assert len(data["affected_areas"]) > 0


def test_future_risk_projections(client):
    """
    Exposes future-risk projections under population growth.
    """
    response = client.get("/decision/future-risk?growth_rate_pct=20.0&time_horizon_years=5&service_type=water")
    assert response.status_code == 200
    data = response.json()

    assert data["service_type"] == "water"
    assert data["time_horizon_years"] == 5
    assert data["growth_rate_pct"] == 20.0
    assert 0.0 <= data["current_risk_score"] <= 100.0
    assert 0.0 <= data["projected_risk_score"] <= 100.0
    assert data["risk_increase"] >= 0.0
    assert data["is_demo_estimate"] is True
    assert len(data["areas_at_risk"]) > 0

    top_risk = data["areas_at_risk"][0]
    assert "area_name" in top_risk
    assert "current_risk_score" in top_risk
    assert "projected_risk_score" in top_risk


# --- Check 5: Invalid inputs are rejected ---
def test_invalid_inputs_rejected(client):
    """
    Confirms invalid inputs yield appropriate client errors (400 or 422).
    """
    # Invalid service type in simulation
    res_bad_service = client.post(
        "/simulations",
        json={"service_type": "interstellar_travel", "latitude": 12.97, "longitude": 77.59},
    )
    assert res_bad_service.status_code in [400, 422]

    # Invalid latitude in simulation
    res_bad_lat = client.post(
        "/simulations",
        json={"service_type": "healthcare", "latitude": 999.0, "longitude": 77.59},
    )
    assert res_bad_lat.status_code in [400, 422]

    # Non-existent service ID in failure simulation
    res_bad_svc_id = client.post(
        "/decision/failure-simulation",
        json={"service_id": 99999999},
    )
    assert res_bad_svc_id.status_code == 400

    # Invalid service type in scenario comparison
    res_bad_sc = client.get("/simulations/scenarios?service_type=crypto_brokerage")
    assert res_bad_sc.status_code == 400


# --- Check 6: Simulation does not permanently modify official data ---
def test_simulation_does_not_modify_official_data(client, db_session):
    """
    Verifies that running what-if simulations and scenario comparisons causes zero
    database mutations.
    """
    svc_count_before = db_session.query(Service).count()
    area_count_before = db_session.query(GeographicArea).count()
    report_count_before = db_session.query(CommunityReport).count()

    # Run what-if simulation
    res1 = client.post(
        "/simulations",
        json={
            "service_type": "water",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "proposed_name": "Temporary Water Node",
            "proposed_capacity": 8000,
        },
    )
    assert res1.status_code == 200

    # Run scenario comparison
    res2 = client.get("/simulations/scenarios?service_type=healthcare")
    assert res2.status_code == 200

    # Run failure simulation
    operational_svc = db_session.query(Service).filter_by(status="operational").first()
    res3 = client.post(
        "/decision/failure-simulation",
        json={"service_id": operational_svc.id},
    )
    assert res3.status_code == 200

    # Close and reopen session to verify clean database state
    db_session.expire_all()
    svc_count_after = db_session.query(Service).count()
    area_count_after = db_session.query(GeographicArea).count()
    report_count_after = db_session.query(CommunityReport).count()

    assert svc_count_before == svc_count_after
    assert area_count_before == area_count_after
    assert report_count_before == report_count_after
