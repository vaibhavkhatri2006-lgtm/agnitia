"""
Tests for Stage 4D: Investment Priority + Failure/Resilience Simulation + Future-Risk Foundation.
Verifies all 6 required Stage 4D checks and ensures zero database corruption or regressions.
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
from app.decision.investment import default_investment_service
from app.decision.resilience import default_resilience_service
from app.decision.future_risk import default_future_risk_service


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


# --- 1. Investment Ranking Test ---
def test_investment_ranking(client):
    """Verifies that investment priority ranking correctly scores and ranks candidate interventions."""
    response = client.post(
        "/decision/investment-priorities",
        json={"service_type": "healthcare", "max_results": 5},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["service_type"] == "healthcare"
    assert data["total_interventions_evaluated"] > 0
    ranked = data["ranked_investments"]
    assert len(ranked) > 0

    top = ranked[0]
    assert top["rank"] == 1
    assert 0.0 <= top["investment_priority_score"] <= 100.0
    assert top["priority_tier"] in ["Highest Priority", "High Priority", "Moderate Priority", "Low Priority"]
    assert top["expected_impact_score"] > 0.0
    assert top["population_affected"] > 0
    assert isinstance(top["rationale"], str)
    assert len(top["primary_drivers"]) > 0

    # Verify descending ordering
    for i in range(len(ranked) - 1):
        assert ranked[i]["investment_priority_score"] >= ranked[i + 1]["investment_priority_score"]

    # Verify cross-sector evaluation when service_type is null
    resp_cross = client.post(
        "/decision/investment-priorities",
        json={"service_type": None, "max_results": 10},
    )
    assert resp_cross.status_code == 200
    assert resp_cross.json()["total_interventions_evaluated"] >= len(ranked)


# --- 2. Failure Simulation Test ---
def test_failure_simulation(client, db_session):
    """Verifies that failure simulation evaluates systemic resilience and identifies critical dependencies."""
    # Test failure of Riverside Health Center (Service 3)
    response = client.post(
        "/decision/failure-simulation",
        json={"service_id": 3, "scope": "city"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["service_id"] == 3
    assert data["service_name"] == "Riverside Health Center"
    assert data["category_code"] == "healthcare"
    assert data["accessibility_drop"] > 0.0
    assert data["coverage_loss"] > 0.0
    assert data["directly_affected_population"] == 18000
    assert data["newly_underserved_population"] == 18000
    assert data["single_point_of_failure"] is True
    assert "Critical Infrastructure" in data["criticality_tier"]
    assert isinstance(data["explanation"], str)
    assert len(data["affected_areas"]) > 0

    # Test failure of a redundant facility (Service 1: Central Metro Hospital)
    resp_redundant = client.post(
        "/decision/failure-simulation",
        json={"service_id": 1, "scope": "city"},
    )
    assert resp_redundant.status_code == 200
    red_data = resp_redundant.json()
    assert red_data["resilience_score"] >= 90.0

    # Database integrity check: counts must be identical before and after
    assert db_session.query(Service).filter_by(id=3).first() is not None
    assert db_session.query(Service).count() == 14


# --- 3. Future Risk Test ---
def test_future_risk(client):
    """Verifies that future risk estimation calculates projected risk under configurable demand growth."""
    response = client.post(
        "/decision/future-risk",
        json={
            "growth_rate_pct": 20.0,
            "time_horizon_years": 5,
            "service_type": "healthcare",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["growth_rate_pct"] == 20.0
    assert data["time_horizon_years"] == 5
    assert 0.0 <= data["current_risk_score"] <= 100.0
    assert 0.0 <= data["projected_risk_score"] <= 100.0
    assert data["projected_risk_score"] >= data["current_risk_score"]
    assert data["risk_increase"] >= 0.0
    assert data["current_risk_category"] in ["Low Risk", "Moderate Risk", "High Risk", "Critical Risk"]
    assert data["projected_risk_category"] in ["Low Risk", "Moderate Risk", "High Risk", "Critical Risk"]
    assert data["risk_trend"] in ["Accelerating Deficit", "Growing Pressure", "Stable"]
    assert len(data["areas_at_risk"]) > 0
    assert data["is_demo_estimate"] is True
    assert "Demo Estimate" in data["label"]
    assert "disclaimer" in data


# --- 4. Deterministic Output Test ---
def test_deterministic_output(client):
    """Verifies that identical inputs produce identical deterministic outputs across all Stage 4D features."""
    # 1. Investment priority determinism
    r1 = client.post("/decision/investment-priorities", json={"service_type": "healthcare", "max_results": 3})
    r2 = client.post("/decision/investment-priorities", json={"service_type": "healthcare", "max_results": 3})
    assert r1.json() == r2.json()

    # 2. Failure simulation determinism
    f1 = client.post("/decision/failure-simulation", json={"service_id": 5})
    f2 = client.post("/decision/failure-simulation", json={"service_id": 5})
    assert f1.json() == f2.json()

    # 3. Future risk determinism
    k1 = client.post("/decision/future-risk", json={"growth_rate_pct": 15.0, "time_horizon_years": 5})
    k2 = client.post("/decision/future-risk", json={"growth_rate_pct": 15.0, "time_horizon_years": 5})
    assert k1.json() == k2.json()


# --- 5. Invalid Input Test ---
def test_invalid_input(client):
    """Verifies that invalid service types, unknown IDs, and out-of-bounds parameters are safely rejected."""
    # Invalid service type for investment
    r_inv = client.post("/decision/investment-priorities", json={"service_type": "space_depot"})
    assert r_inv.status_code == 400
    assert "unsupported service type" in r_inv.json()["detail"].lower()

    # Non-existent service ID for failure simulation
    r_fail = client.post("/decision/failure-simulation", json={"service_id": 99999})
    assert r_fail.status_code == 400
    assert "not found" in r_fail.json()["detail"].lower()

    # Out of bounds growth rate for future risk
    r_risk_pct = client.post("/decision/future-risk", json={"growth_rate_pct": 250.0})
    assert r_risk_pct.status_code in [400, 422]

    # Out of bounds time horizon
    r_risk_yr = client.post("/decision/future-risk", json={"time_horizon_years": 0})
    assert r_risk_yr.status_code in [400, 422]


# --- 6. Stage 4A / 4B / 4C Regression and Database Integrity Test ---
def test_stage_4_regressions_and_db_integrity(client, db_session):
    """Verifies that all earlier Stage 4 pipelines (4A, 4B, 4C) continue functioning with zero corruption."""
    counts_before = {
        "services": db_session.query(Service).count(),
        "capacities": db_session.query(ServiceCapacity).count(),
        "areas": db_session.query(GeographicArea).count(),
        "pop": db_session.query(PopulationCell).count(),
        "reports": db_session.query(CommunityReport).count(),
    }

    # Stage 4A: Candidates
    r_cand = client.get("/decision/candidates?service_type=healthcare")
    assert r_cand.status_code == 200
    assert r_cand.json()["valid_candidates_count"] > 0

    # Stage 4B: Recommendations
    r_rec = client.post("/recommendations", json={"service_type": "healthcare"})
    assert r_rec.status_code == 200
    assert len(r_rec.json()["ranked_candidates"]) > 0

    # Stage 4C: Simulations
    r_sim = client.post("/simulations", json={"service_type": "healthcare", "candidate_id": "cand-healthcare-9-centroid"})
    assert r_sim.status_code == 200
    assert r_sim.json()["impact"]["coverage_improvement"] > 0.0

    # Assert database counts remain strictly unmutated
    assert db_session.query(Service).count() == counts_before["services"]
    assert db_session.query(ServiceCapacity).count() == counts_before["capacities"]
    assert db_session.query(GeographicArea).count() == counts_before["areas"]
    assert db_session.query(PopulationCell).count() == counts_before["pop"]
    assert db_session.query(CommunityReport).count() == counts_before["reports"]
