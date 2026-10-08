"""
Stage 5 Verification Tests — Frontend Integration Foundation.
Verifies:
1. Backend startup and /health
2. Login and token issuance
3. /auth/me profile inspection
4. Invalid/expired token rejection (401)
5. Server-side RBAC enforcement (403)
6. Safe credentialed CORS configuration
7. Standardized JSON error response structures (400, 401, 403, 404, 422, 500)
8. All documented core APIs (localities, services, analytics, candidates, recommendations, simulations, investments, resilience, future risk)
9. Frontend-safe JSON formats and demo-mode determinism
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def test_stage5_startup_and_health():
    """Check 1 & 2: Backend starts and /health returns 200 OK with healthy status."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    root_data = res_root.json()
    assert "CivicPulse" in root_data["app"]
    assert root_data["health_check"] == "/health"
    assert root_data["auth_login"] == "/auth/login"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["database"] == "connected"


def test_stage5_login_and_auth_me():
    """Check 3 & 4: Login works with demo credentials and /auth/me returns caller profile."""
    # Login as citizen
    login_res = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["token_type"].lower() == "bearer"
    assert login_data["user"]["email"] == "citizen@example.com"
    assert login_data["user"]["role"] == "citizen"

    token = login_data["access_token"]

    # Verify /auth/me with bearer token
    me_res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "citizen@example.com"
    assert me_data["role"] == "citizen"
    assert "data:read" in me_data["permissions"]


def test_stage5_invalid_token_returns_401():
    """Check 5: Missing or invalid token returns 401 with standard error format."""
    # Missing token
    res_missing = client.get("/auth/me")
    assert res_missing.status_code == 401
    err_missing = res_missing.json()
    assert "detail" in err_missing
    assert err_missing["status_code"] == 401
    assert err_missing["error_code"] == "HTTP_401"

    # Malformed token
    res_malformed = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert res_malformed.status_code == 401
    err_malformed = res_malformed.json()
    assert "detail" in err_malformed
    assert err_malformed["status_code"] == 401
    assert err_malformed["error_code"] == "HTTP_401"


def test_stage5_unauthorized_role_returns_403():
    """Check 6: Unauthorized role returns 403 with standard error format."""
    # Citizen attempts to access authority endpoint
    login_res = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    )
    token = login_res.json()["access_token"]

    res_auth = client.get(
        "/auth/verify-role/authority",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_auth.status_code == 403
    err_data = res_auth.json()
    assert "detail" in err_data
    assert "Access denied" in err_data["detail"]
    assert err_data["status_code"] == 403
    assert err_data["error_code"] == "HTTP_403"


def test_stage5_cors_configuration():
    """Check 7: CORS works for allowed frontend origins without unsafe credentials wildcard."""
    # Ensure cors_origins is safe
    assert "*" not in settings.cors_origins
    assert "http://localhost:5173" in settings.cors_origins

    # Preflight OPTIONS request from allowed origin
    preflight_res = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight_res.status_code == 200
    assert preflight_res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert preflight_res.headers.get("access-control-allow-credentials") == "true"

    # GET request with allowed origin
    health_res = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert health_res.status_code == 200
    assert health_res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert health_res.headers.get("access-control-allow-credentials") == "true"

    # Unauthorized origin should NOT receive allow-origin header
    unauthorized_res = client.get(
        "/health",
        headers={"Origin": "http://untrusted-external-site.com"},
    )
    assert unauthorized_res.status_code == 200
    assert unauthorized_res.headers.get("access-control-allow-origin") is None


def test_stage5_consistent_error_structure():
    """Check: Standard JSON error structures for 400, 401, 403, 404, 422, 500."""
    # 400 Bad Request
    res_400 = client.post(
        "/decision/candidates/generate",
        json={"service_type": "invalid_service_type"},
    )
    assert res_400.status_code == 400
    data_400 = res_400.json()
    assert "detail" in data_400
    assert data_400["status_code"] == 400
    assert data_400["error_code"] == "HTTP_400"

    # 401 Unauthorized
    res_401 = client.get("/auth/me")
    assert res_401.status_code == 401
    data_401 = res_401.json()
    assert "detail" in data_401
    assert data_401["status_code"] == 401
    assert data_401["error_code"] == "HTTP_401"

    # 403 Forbidden
    login_citizen = client.post(
        "/auth/login",
        json={"email": "citizen@example.com", "password": "Citizen123!"},
    ).json()["access_token"]
    res_403 = client.get(
        "/auth/verify-role/admin",
        headers={"Authorization": f"Bearer {login_citizen}"},
    )
    assert res_403.status_code == 403
    data_403 = res_403.json()
    assert "detail" in data_403
    assert data_403["status_code"] == 403
    assert data_403["error_code"] == "HTTP_403"

    # 404 Not Found
    res_404 = client.get("/services/999999")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert "detail" in data_404
    assert data_404["status_code"] == 404
    assert data_404["error_code"] == "HTTP_404"

    # 422 Validation Error
    res_422 = client.post(
        "/decision/future-risk",
        json={"growth_rate_pct": "not-a-number"},
    )
    assert res_422.status_code == 422
    data_422 = res_422.json()
    assert "detail" in data_422
    assert "errors" in data_422
    assert data_422["status_code"] == 422
    assert data_422["error_code"] == "VALIDATION_ERROR"

    # 500 Internal Server Error (via debug test route)
    res_500 = client.get("/test-error-500")
    assert res_500.status_code == 500
    data_500 = res_500.json()
    assert "detail" in data_500
    assert data_500["status_code"] == 500
    assert data_500["error_code"] == "INTERNAL_SERVER_ERROR"


def test_stage5_all_documented_core_apis():
    """Check 8: All documented core APIs return valid, schema-compliant JSON responses."""
    # 1. Localities (Geographic Areas)
    res_areas = client.get("/areas")
    assert res_areas.status_code == 200
    areas = res_areas.json()
    assert isinstance(areas, list)
    assert len(areas) >= 5
    first_area = areas[0]
    assert "id" in first_area and "name" in first_area and "population" in first_area

    # Specific area
    res_area = client.get(f"/areas/{first_area['id']}")
    assert res_area.status_code == 200
    assert res_area.json()["id"] == first_area["id"]

    # 2. Services & Categories
    res_cats = client.get("/services/categories")
    assert res_cats.status_code == 200
    cats = res_cats.json()
    assert len(cats) >= 5
    cat_codes = [c["code"] for c in cats]
    assert "healthcare" in cat_codes and "education" in cat_codes

    res_services = client.get("/services?category_code=healthcare")
    assert res_services.status_code == 200
    services = res_services.json()
    assert len(services) >= 2
    assert all(s["category_code"] == "healthcare" for s in services)
    assert "latitude" in services[0] and "longitude" in services[0]

    first_srv = services[0]
    res_srv_detail = client.get(f"/services/{first_srv['id']}")
    assert res_srv_detail.status_code == 200
    assert res_srv_detail.json()["id"] == first_srv["id"]

    # 3. Accessibility & Gap Analytics
    res_analytics_areas = client.get("/analytics/areas")
    assert res_analytics_areas.status_code == 200
    analytics_areas = res_analytics_areas.json()
    assert len(analytics_areas) >= 5
    assert "composite_accessibility_score" in analytics_areas[0]
    assert "composite_gap_score" in analytics_areas[0]

    # Deserts
    res_deserts = client.get("/analytics/deserts")
    assert res_deserts.status_code == 200
    assert isinstance(res_deserts.json(), list)

    # 4. Candidate Locations (4A)
    res_cand = client.get("/decision/candidates?service_type=healthcare")
    assert res_cand.status_code == 200
    cand_data = res_cand.json()
    assert cand_data["service_type"] == "healthcare"
    assert cand_data["valid_candidates_count"] > 0

    # 5. Recommendations (4B)
    res_rec = client.get("/recommendations?service_type=healthcare")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert len(rec_data["ranked_candidates"]) > 0
    top_cand = rec_data["ranked_candidates"][0]
    assert top_cand["rank"] == 1
    assert "recommendation_score" in top_cand

    # 6. Simulations (4C)
    res_sim = client.post(
        "/simulations",
        json={"service_type": "healthcare", "candidate_id": top_cand["candidate_id"]},
    )
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert "impact" in sim_data
    assert "accessibility_improvement" in sim_data["impact"]

    # 7. Investment Priorities (4D)
    res_inv = client.get("/decision/investment-priorities?service_type=healthcare")
    assert res_inv.status_code == 200
    inv_data = res_inv.json()
    assert len(inv_data["ranked_investments"]) > 0
    assert "investment_priority_score" in inv_data["ranked_investments"][0]

    # 8. Failure Simulation (4D)
    res_fail = client.post(
        "/decision/failure-simulation",
        json={"service_id": first_srv["id"]},
    )
    assert res_fail.status_code == 200
    fail_data = res_fail.json()
    assert "resilience_score" in fail_data

    # 9. Future Risk (4D)
    res_risk = client.get("/decision/future-risk?growth_rate_pct=15.0&time_horizon_years=5")
    assert res_risk.status_code == 200
    risk_data = res_risk.json()
    assert risk_data["is_demo_estimate"] is True
    assert "projected_risk_score" in risk_data


def test_stage5_frontend_safe_and_deterministic():
    """Check 9: Deterministic repeatability without external network dependencies."""
    # Verify deterministic output across identical calls
    res1 = client.get("/decision/candidates?service_type=education").json()
    res2 = client.get("/decision/candidates?service_type=education").json()
    assert res1 == res2

    # Verify recommendations determinism
    rec1 = client.get("/recommendations?service_type=education").json()
    rec2 = client.get("/recommendations?service_type=education").json()
    assert rec1 == rec2

    # Verify investment ranking determinism
    inv1 = client.get("/decision/investment-priorities?service_type=education").json()
    inv2 = client.get("/decision/investment-priorities?service_type=education").json()
    assert inv1 == inv2
