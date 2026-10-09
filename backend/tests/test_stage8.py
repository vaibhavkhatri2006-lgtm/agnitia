"""
CivicPulse Stage 8 — Planner Command Center Backend Tests.
Validates:
1. Underserved Ranking API (rank, area, accessibility, gap, population, main service gap, priority)
2. Service Comparison API (healthcare, education, transport, water, market)
3. Capacity Pressure API (demand, capacity, pressure, status)
4. Equity & Reality Gap API (equity score, contributing factors, map access, real-world score, reality gap, confidence)
5. Recommendation API (recommended candidate, score, rank, reasons, expected impact, confidence)
6. Authority Permission / RBAC checks (authority/admin allowed, citizen rejected with 403)
7. Unified Overview / Dashboard bundle API
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_token(email: str, password: str) -> str:
    """Helper to authenticate and fetch bearer token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def authority_token():
    return get_token("authority@example.com", "Authority123!")


@pytest.fixture(scope="module")
def admin_token():
    return get_token("admin@example.com", "Admin123!")


@pytest.fixture(scope="module")
def citizen_token():
    return get_token("citizen@example.com", "Citizen123!")


def test_planner_rankings_api(authority_token):
    """Check 1: Underserved ranking API returns prioritized localities with all required fields."""
    res = client.get(
        "/planner/rankings?limit=5",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Rankings failed: {res.text}"
    data = res.json()

    assert "total_areas_evaluated" in data
    assert "rankings" in data
    assert len(data["rankings"]) > 0

    first = data["rankings"][0]
    assert first["rank"] == 1
    assert "area" in first
    assert "area_id" in first
    assert "accessibility" in first
    assert "gap" in first
    assert "population" in first
    assert "main_service_gap" in first
    assert "priority" in first
    assert first["priority"] in ["Critical", "High", "Medium", "Low"]

    # Verify deterministic ordering: rank 1 has highest gap
    if len(data["rankings"]) > 1:
        assert data["rankings"][0]["gap"] >= data["rankings"][1]["gap"]


def test_planner_service_comparison_api(authority_token):
    """Check 2: Service comparison API compares healthcare, education, transport, water, and market."""
    # City-wide comparison
    res = client.get(
        "/planner/service-comparison",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Service comparison failed: {res.text}"
    data = res.json()

    assert "services" in data
    services = data["services"]
    assert len(services) == 5

    service_codes = {s["service_type"] for s in services}
    expected_codes = {"healthcare", "education", "transport", "water", "market"}
    assert service_codes == expected_codes

    for s in services:
        assert "service_name" in s
        assert "accessibility_score" in s
        assert "gap_score" in s
        assert "status" in s
        assert "capacity_status" in s
        assert "rank" in s

    # Area-specific comparison
    res_area = client.get(
        "/planner/service-comparison?area_id=1",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res_area.status_code == 200
    data_area = res_area.json()
    assert data_area["area_id"] == 1
    assert len(data_area["services"]) == 5


def test_planner_capacity_pressure_api(authority_token):
    """Check 3: Capacity pressure API returns demand, capacity, pressure, and status."""
    res = client.get(
        "/planner/capacity-pressure?service_type=healthcare",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Capacity pressure failed: {res.text}"
    data = res.json()

    assert "demand" in data
    assert "capacity" in data
    assert "pressure" in data
    assert "status" in data
    assert data["demand"] > 0
    assert data["status"] in ["Low", "Moderate", "High", "Critical"]

    assert "items" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "demand" in item
    assert "capacity" in item
    assert "pressure" in item
    assert "status" in item


def test_planner_equity_reality_gap_api(authority_token):
    """Check 4: Equity and Reality Gap API returns equity score, factors, map score, real-world score, reality gap, and confidence."""
    res = client.get(
        "/planner/equity-reality-gap?category_code=healthcare",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Equity & reality gap failed: {res.text}"
    data = res.json()

    # Equity requirements
    assert "equity_score" in data
    assert "main_contributing_factors" in data
    assert isinstance(data["main_contributing_factors"], list)
    assert len(data["main_contributing_factors"]) > 0

    # Reality Gap requirements
    assert "map_access_score" in data
    assert "real_world_score" in data
    assert "reality_gap" in data
    assert "confidence" in data
    assert data["confidence"] > 0.0

    # Alias endpoints
    equity_res = client.get("/planner/equity", headers={"Authorization": f"Bearer {authority_token}"})
    assert equity_res.status_code == 200
    assert "equity_score" in equity_res.json()

    reality_res = client.get("/planner/reality-gap", headers={"Authorization": f"Bearer {authority_token}"})
    assert reality_res.status_code == 200
    assert "reality_gap" in reality_res.json()


def test_planner_recommendation_api(authority_token):
    """Check 5: Recommendation API returns recommended candidate, score, rank, reasons, expected impact, and confidence."""
    res = client.get(
        "/planner/recommendations?service_type=healthcare",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Recommendations failed: {res.text}"
    data = res.json()

    assert data["service_type"] == "healthcare"
    assert data["total_candidates_evaluated"] > 0
    assert data["recommended_candidate"] is not None

    cand = data["recommended_candidate"]
    assert "candidate_id" in cand
    assert "latitude" in cand
    assert "longitude" in cand
    assert "area_name" in cand

    assert data["score"] is not None
    assert data["score"] > 0.0
    assert data["rank"] == 1
    assert "reasons" in data
    assert len(data["reasons"]) > 0

    # Expected impact
    impact = data["expected_impact"]
    assert impact is not None
    assert "accessibility_improvement" in impact
    assert "coverage_gain" in impact
    assert "impact_score" in impact
    assert "summary" in impact

    # Confidence
    assert data["confidence"] is not None
    assert data["confidence"] > 0.0


def test_planner_authority_permission_check(authority_token, admin_token, citizen_token):
    """Check 6: Server-side RBAC enforces authority/admin access while restricting citizens (returns 403)."""
    endpoints = [
        "/planner/rankings",
        "/planner/service-comparison",
        "/planner/capacity-pressure",
        "/planner/equity-reality-gap",
        "/planner/recommendations",
        "/planner/overview",
    ]

    for ep in endpoints:
        # Authority succeeds (200)
        auth_resp = client.get(ep, headers={"Authorization": f"Bearer {authority_token}"})
        assert auth_resp.status_code == 200, f"Authority should have access to {ep}: {auth_resp.text}"

        # Admin succeeds (200)
        admin_resp = client.get(ep, headers={"Authorization": f"Bearer {admin_token}"})
        assert admin_resp.status_code == 200, f"Admin should have access to {ep}: {admin_resp.text}"

        # Citizen is forbidden (403)
        cit_resp = client.get(ep, headers={"Authorization": f"Bearer {citizen_token}"})
        assert cit_resp.status_code == 403, f"Citizen must be forbidden (403) from {ep}"

        # Unauthenticated is rejected (401)
        unauth_resp = client.get(ep)
        assert unauth_resp.status_code == 401, f"Unauthenticated request must return 401 for {ep}"


def test_planner_overview_dashboard_bundle(authority_token):
    """Check 7: Unified overview bundle delivers all planner dashboard metrics in a single payload."""
    res = client.get(
        "/planner/overview",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res.status_code == 200, f"Overview failed: {res.text}"
    data = res.json()

    assert "total_areas_monitored" in data
    assert "most_underserved_areas" in data
    assert "service_comparison" in data
    assert "capacity_pressure" in data
    assert "top_recommendation" in data
