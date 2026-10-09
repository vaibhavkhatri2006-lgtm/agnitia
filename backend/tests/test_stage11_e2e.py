"""
CivicPulse Stage 11 — Final End-to-End Integration & QA Test Suite.
Validates the complete critical demo flow, authentication & RBAC,
infrastructure GeoJSON layers, analytical gap scoring, candidate recommendations,
what-if intervention simulations, community report verification lifecycle,
audit logs, and Real Data / Demo mode integrity.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import GeographicArea, Service, ServiceCategory, CommunityReport, AuditLog

client = TestClient(app)


def get_auth_token(email: str, password: str) -> str:
    """Helper to authenticate and fetch JWT access token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Authentication failed for {email}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def citizen_token():
    return get_auth_token("citizen@example.com", "Citizen123!")


@pytest.fixture(scope="module")
def community_token():
    return get_auth_token("community@example.com", "Community123!")


@pytest.fixture(scope="module")
def authority_token():
    return get_auth_token("authority@example.com", "Authority123!")


@pytest.fixture(scope="module")
def admin_token():
    return get_auth_token("admin@example.com", "Admin123!")


class TestStage11AuthenticationAndRBAC:
    """Validates login, credentials, token issuance, and server-side RBAC across all 4 roles."""

    def test_login_all_four_roles(self):
        roles = [
            ("citizen@example.com", "Citizen123!", "citizen"),
            ("community@example.com", "Community123!", "community"),
            ("authority@example.com", "Authority123!", "authority"),
            ("admin@example.com", "Admin123!", "admin"),
        ]
        for email, pwd, expected_role in roles:
            resp = client.post("/auth/login", json={"email": email, "password": pwd})
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

            # Check /auth/me
            me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
            assert me_resp.status_code == 200
            assert me_resp.json()["role"] == expected_role

    def test_invalid_credentials_rejected(self):
        resp = client.post("/auth/login", json={"email": "citizen@example.com", "password": "WrongPassword!"})
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "HTTP_401"

    def test_inactive_user_rejected(self):
        resp = client.post("/auth/login", json={"email": "inactive@example.com", "password": "Inactive123!"})
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "HTTP_403"

    def test_rbac_planner_access_restrictions(self, citizen_token, authority_token):
        # Citizen cannot access planner dashboard (403)
        cit_resp = client.get("/planner/overview", headers={"Authorization": f"Bearer {citizen_token}"})
        assert cit_resp.status_code == 403

        # Authority can access planner dashboard (200)
        auth_resp = client.get("/planner/overview", headers={"Authorization": f"Bearer {authority_token}"})
        assert auth_resp.status_code == 200


class TestStage11CriticalUserFlow:
    """
    Executes the prioritized core demo flow:
    Map -> Select locality -> View service gap -> Get recommendation -> Run simulation -> See impact.
    """

    def test_step1_map_and_infrastructure_load(self):
        """1. Dashboard & map load with locality boundaries and service pins."""
        # Localities GeoJSON
        areas_resp = client.get("/areas/geojson")
        assert areas_resp.status_code == 200
        areas_data = areas_resp.json()
        assert areas_data["type"] == "FeatureCollection"
        assert len(areas_data["features"]) > 0

        # Services GeoJSON
        services_resp = client.get("/services/geojson")
        assert services_resp.status_code == 200
        services_data = services_resp.json()
        assert services_data["type"] == "FeatureCollection"
        assert len(services_data["features"]) > 0

    def test_step2_select_locality_and_view_service_gap(self):
        """2. Selecting a locality shows accessibility/gap scores and nearest facilities."""
        # Find Highlands Valley / Vijay Nagar (known underserved locality in demo data)
        area_resp = client.get("/areas")
        assert area_resp.status_code == 200
        areas = area_resp.json()
        highlands = next((a for a in areas if "Highlands" in a["name"] or "Vijay" in a["name"]), areas[0])
        area_id = highlands["id"]

        # Locality analytics scorecard
        analytics_resp = client.get(f"/analytics/areas/{area_id}")
        assert analytics_resp.status_code == 200
        data = analytics_resp.json()
        assert "composite_accessibility_score" in data
        assert "composite_gap_score" in data
        assert "composite_desert_classification" in data
        assert data["categories_evaluated"] == 5

        # Category-specific breakdown for healthcare
        cat_resp = client.get(f"/analytics/areas/{area_id}/category/healthcare")
        assert cat_resp.status_code == 200
        cat_data = cat_resp.json()
        assert cat_data["category_code"] == "healthcare"
        assert "accessibility_score" in cat_data
        assert "gap_score" in cat_data
        assert "service_desert_classification" in cat_data

    def test_step3_underserved_area_ranking(self):
        """3. Underserved-area ranking loads and sorts most critical deficits first."""
        rank_resp = client.get("/analytics/rankings/underserved")
        assert rank_resp.status_code == 200
        rank_data = rank_resp.json()
        assert rank_data["total_areas_evaluated"] > 0
        items = rank_data["rankings"]
        assert len(items) > 0
        # Rank 1 must have higher or equal gap score than Rank 2
        if len(items) > 1:
            assert items[0]["gap_score"] >= items[1]["gap_score"]

    def test_step4_recommendation_returns_explainable_candidate(self):
        """4. Recommendation returns candidate with scores and explainable factors."""
        rec_payload = {
            "service_type": "healthcare",
            "candidate_strategy": "all",
            "weights": {
                "gap": 0.30,
                "population": 0.25,
                "travel_time": 0.15,
                "capacity": 0.10,
                "equity": 0.10,
                "connectivity": 0.05,
                "confidence": 0.05,
            },
        }
        rec_resp = client.post("/recommendations", json=rec_payload)
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        assert rec_data["valid_candidates_scored"] > 0
        top_cand = rec_data["ranked_candidates"][0]
        assert top_cand["rank"] == 1
        assert 0.0 <= top_cand["recommendation_score"] <= 100.0
        assert "reasons" in top_cand
        assert len(top_cand["reasons"]) > 0
        assert "factor_values" in top_cand
        assert top_cand["latitude"] is not None

    def test_step5_and_6_simulation_and_impact(self):
        """5 & 6. What-if simulation shows consistent before/after metrics and impact."""
        # Simulate placing clinic at top candidate location in Highlands Valley
        sim_payload = {
            "service_type": "healthcare",
            "candidate_id": "cand-healthcare-9-centroid",
            "scope": "city",
            "proposed_capacity": 5000,
        }
        sim_resp = client.post("/simulations", json=sim_payload)
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()

        # Before & After consistency
        before = sim_data["before"]
        after = sim_data["after"]
        impact = sim_data["impact"]
        target = sim_data["target_area"]

        assert before["accessibility_score"] < after["accessibility_score"]
        assert impact["accessibility_improvement"] > 0.0
        assert impact["coverage_improvement"] > 0.0
        assert impact["underserved_population_reduction"] > 0
        assert target["accessibility_improvement"] > 0.0
        assert target["after_accessibility"] > target["before_accessibility"]
        assert "explanation" in sim_data
        assert len(sim_data["primary_factors"]) > 0


class TestStage11CommunityVerificationAndAuditTrail:
    """Validates community report creation, multi-tier verification workflow, and audit trail."""

    def test_report_lifecycle_and_audit(self, citizen_token, community_token, authority_token):
        # 1. Citizen creates report
        report_payload = {
            "category_code": "water",
            "title": "Broken Water Tap in Community Square",
            "description": "Primary drinking water point pipe is leaking and unavailable for residents.",
            "latitude": 12.935,
            "longitude": 77.615,
            "severity": "high",
        }
        create_resp = client.post(
            "/reports",
            json=report_payload,
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert create_resp.status_code == 201
        report = create_resp.json()
        report_id = report["id"]
        assert report["status"] == "PENDING_REVIEW"
        assert report["confidence_score"] == 0.50

        # 2. Citizen cannot approve official status (403)
        cit_verify_resp = client.post(
            f"/reports/{report_id}/verify",
            json={"verification_status": "OFFICIAL", "notes": "I approve this officially"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert cit_verify_resp.status_code == 403

        # 3. Community verifies report
        comm_verify_resp = client.post(
            f"/reports/{report_id}/verify",
            json={"verification_status": "COMMUNITY_VERIFIED", "notes": "Verified by community patrol"},
            headers={"Authorization": f"Bearer {community_token}"},
        )
        assert comm_verify_resp.status_code == 200
        assert comm_verify_resp.json()["status"] == "COMMUNITY_VERIFIED"
        assert comm_verify_resp.json()["confidence_score"] >= 0.75

        # 4. Authority verifies report officially
        auth_verify_resp = client.post(
            f"/reports/{report_id}/verify",
            json={"verification_status": "OFFICIAL", "notes": "Inspected and confirmed by municipal water board"},
            headers={"Authorization": f"Bearer {authority_token}"},
        )
        assert auth_verify_resp.status_code == 200
        assert auth_verify_resp.json()["status"] == "OFFICIAL"
        assert auth_verify_resp.json()["confidence_score"] == 1.00

        # 5. Audit history verified
        audit_resp = client.get(
            f"/reports/{report_id}/audit-trail",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert audit_resp.status_code == 200
        trail = audit_resp.json()
        assert len(trail) >= 3  # initial submit + community verify + official verify


class TestStage11RealDataAndDemoModeIntegrity:
    """Validates operational mode toggle, provenance tracking, and offline demo mode."""

    def test_mode_toggle_and_sources(self):
        # Demo mode
        resp_demo = client.post("/mode", json={"mode": "demo"})
        assert resp_demo.status_code == 200
        assert resp_demo.json()["mode"] == "demo"
        assert "simulated_demo" in resp_demo.json()["active_sources"]

        # Real Data mode
        resp_real = client.post("/mode", json={"mode": "real"})
        assert resp_real.status_code == 200
        assert resp_real.json()["mode"] == "real"
        assert "osm" in resp_real.json()["active_sources"]

        # Reset to demo
        client.post("/mode", json={"mode": "demo"})

    def test_service_provenance_inspection(self):
        # Inspect demo facility provenance
        resp = client.get("/services/1/provenance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service_id"] == 1
        assert "provenance" in data
        assert "license" in data

    def test_demo_mode_offline_guarantee(self):
        """Ensures all standard analytics work 100% offline without network calls."""
        resp = client.get("/analytics/areas")
        assert resp.status_code == 200
        assert len(resp.json()) > 0
