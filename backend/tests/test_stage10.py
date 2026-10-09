"""
CivicPulse Stage 10 — Multi-Scale Experience Backend Tests.
Validates the 6 required checks:
1. Switching scope changes metrics when the underlying data differs.
2. Permissions are respected.
3. API accepts and validates geographic hierarchy.
4. Parent-child relationships are valid.
5. Ranking works for each supported scope.
6. Unavailable data returns a safe no-data response.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import GeographicArea

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
def citizen_token():
    return get_token("citizen@example.com", "Citizen123!")


# --- Check 1: Switching scope changes metrics when the underlying data differs ---
def test_switching_scope_changes_metrics():
    """
    Verifies that querying different geographic scopes (neighbourhood vs ward vs city)
    produces distinct, scale-specific aggregate metrics and area sets.
    """
    res_neigh = client.get("/analytics/multiscale?scope=neighbourhood")
    assert res_neigh.status_code == 200
    data_neigh = res_neigh.json()
    assert data_neigh["available"] is True
    assert data_neigh["scope"] == "neighbourhood"
    assert data_neigh["total_areas"] == 5

    res_ward = client.get("/analytics/multiscale?scope=ward")
    assert res_ward.status_code == 200
    data_ward = res_ward.json()
    assert data_ward["available"] is True
    assert data_ward["scope"] == "ward"
    assert data_ward["total_areas"] == 4

    res_city = client.get("/analytics/multiscale?scope=city")
    assert res_city.status_code == 200
    data_city = res_city.json()
    assert data_city["available"] is True
    assert data_city["scope"] == "city"
    assert data_city["total_areas"] == 1

    # Metrics differ between granularities
    assert data_neigh["total_areas"] != data_ward["total_areas"]
    assert data_ward["total_areas"] != data_city["total_areas"]
    assert len(data_neigh["areas"]) == 5
    assert len(data_ward["areas"]) == 4
    assert len(data_city["areas"]) == 1

    # Area names match the appropriate scale
    neigh_names = [a["name"] for a in data_neigh["areas"]]
    ward_names = [a["name"] for a in data_ward["areas"]]
    assert any(name in neigh_names for name in ["Rajwada", "Downtown Core"])
    assert any(name in ward_names for name in ["Zone 1 - Rajwada Central", "District 1 - Central Ward"])


# --- Check 2: Permissions are respected ---
def test_permissions_respected(authority_token, citizen_token):
    """
    Ensures authority and admin access are permitted while citizen/unauthenticated
    requests are properly enforced via RBAC.
    """
    # Authority succeeds
    res_auth = client.get(
        "/planner/rankings?scope=neighbourhood",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res_auth.status_code == 200
    assert len(res_auth.json()["rankings"]) > 0

    # Citizen forbidden (403)
    res_citizen = client.get(
        "/planner/rankings?scope=neighbourhood",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_citizen.status_code == 403

    # Unauthenticated rejected (401)
    res_anon = client.get("/planner/rankings?scope=neighbourhood")
    assert res_anon.status_code == 401

    # Public multi-scale discovery endpoints do not require auth
    res_scopes = client.get("/areas/scopes")
    assert res_scopes.status_code == 200
    res_multi = client.get("/analytics/multiscale?scope=city")
    assert res_multi.status_code == 200


# --- Check 3: API accepts and validates geographic hierarchy ---
def test_api_accepts_and_validates_hierarchy():
    """
    Verifies tree construction and hierarchy relationship validation API.
    """
    # Tree inspection
    res_tree = client.get("/areas/hierarchy")
    assert res_tree.status_code == 200
    tree = res_tree.json()
    assert len(tree) >= 1  # Root city node

    root = tree[0]
    assert root["area_type"] == "city"
    assert root["name"] in ["Indore", "Metro City"]
    assert len(root["children"]) >= 4  # Districts

    district = root["children"][0]
    assert district["area_type"] == "ward"
    assert len(district["children"]) >= 1  # Neighbourhoods

    # Relationship validation API
    # Valid: city contains ward
    res_val1 = client.post(
        "/areas/hierarchy/validate-relationship",
        json={"parent_type": "city", "child_type": "ward"},
    )
    assert res_val1.status_code == 200
    assert res_val1.json()["is_valid"] is True

    # Valid: ward contains neighbourhood
    res_val2 = client.post(
        "/areas/hierarchy/validate-relationship",
        json={"parent_type": "ward", "child_type": "neighbourhood"},
    )
    assert res_val2.status_code == 200
    assert res_val2.json()["is_valid"] is True

    # Invalid: neighbourhood cannot contain city
    res_inv1 = client.post(
        "/areas/hierarchy/validate-relationship",
        json={"parent_type": "neighbourhood", "child_type": "city"},
    )
    assert res_inv1.status_code == 200
    assert res_inv1.json()["is_valid"] is False

    # Invalid: ward cannot contain ward
    res_inv2 = client.post(
        "/areas/hierarchy/validate-relationship",
        json={"parent_type": "ward", "child_type": "ward"},
    )
    assert res_inv2.status_code == 200
    assert res_inv2.json()["is_valid"] is False


# --- Check 4: Parent-child relationships are valid ---
def test_parent_child_relationships_are_valid():
    """
    Audits the current geographic database to verify that all parent-child relationships
    are structurally sound, non-circular, and properly ordered.
    """
    res = client.get("/areas/hierarchy/validate")
    assert res.status_code == 200
    report = res.json()

    assert report["status"] == "valid"
    assert report["is_valid"] is True
    assert report["orphan_count"] == 0
    assert report["circular_references_count"] == 0
    assert report["errors"] == []
    assert report["total_areas"] >= 10
    assert report["root_areas_count"] >= 1
    assert report["max_depth"] >= 3  # city -> ward -> neighbourhood


# --- Check 5: Ranking works for each supported scope ---
def test_ranking_works_for_supported_scopes(authority_token):
    """
    Verifies that underserved rankings can be filtered by scope across
    both public analytics and planner command center endpoints.
    """
    # Neighbourhood ranking
    res_n = client.get("/analytics/rankings/underserved?scope=neighbourhood")
    assert res_n.status_code == 200
    data_n = res_n.json()
    assert data_n["total_areas_evaluated"] == 5
    for item in data_n["rankings"]:
        assert item["area_type"] == "neighbourhood"

    # Ward ranking
    res_w = client.get("/analytics/rankings/underserved?scope=ward")
    assert res_w.status_code == 200
    data_w = res_w.json()
    assert data_w["total_areas_evaluated"] == 4
    for item in data_w["rankings"]:
        assert item["area_type"] in ["ward", "district"]

    # City ranking
    res_c = client.get("/analytics/rankings/underserved?scope=city")
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert data_c["total_areas_evaluated"] == 1
    for item in data_c["rankings"]:
        assert item["area_type"] == "city"

    # Planner scope ranking
    res_p_n = client.get(
        "/planner/rankings?scope=neighbourhood",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res_p_n.status_code == 200
    assert res_p_n.json()["total_areas_evaluated"] == 5

    res_p_w = client.get(
        "/planner/rankings?scope=ward",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res_p_w.status_code == 200
    assert res_p_w.json()["total_areas_evaluated"] == 4


# --- Check 6: Unavailable data returns a safe no-data response ---
def test_unavailable_data_returns_safe_nodata_response(authority_token):
    """
    Verifies that requesting higher, unpopulated geographic scales (region, country, global)
    returns explicit, structured no-data responses without inventing data.
    """
    # 1. Scopes metadata endpoint confirms unavailability
    res_scopes = client.get("/areas/scopes")
    assert res_scopes.status_code == 200
    scopes_data = res_scopes.json()
    assert "region" in scopes_data["unavailable_scopes"]
    assert "country" in scopes_data["unavailable_scopes"]
    assert "global" in scopes_data["unavailable_scopes"]

    # 2. Multi-scale analytics returns explicit no-data response for region
    res_region = client.get("/analytics/multiscale?scope=region")
    assert res_region.status_code == 200
    data_reg = res_region.json()
    assert data_reg["available"] is False
    assert data_reg["status"] == "no_data"
    assert data_reg["total_areas"] == 0
    assert data_reg["total_population"] == 0
    assert data_reg["areas"] == []
    assert "unavailable" in data_reg["message"].lower()

    # 3. Country scale returns explicit no-data response
    res_country = client.get("/analytics/multiscale?scope=country")
    assert res_country.status_code == 200
    assert res_country.json()["status"] == "no_data"
    assert res_country.json()["available"] is False

    # 4. Global scale returns explicit no-data response
    res_global = client.get("/analytics/multiscale?scope=global")
    assert res_global.status_code == 200
    assert res_global.json()["status"] == "no_data"
    assert res_global.json()["available"] is False

    # 5. Public underserved ranking returns safe empty response
    res_rank_reg = client.get("/analytics/rankings/underserved?scope=region")
    assert res_rank_reg.status_code == 200
    assert res_rank_reg.json()["total_areas_evaluated"] == 0
    assert res_rank_reg.json()["rankings"] == []

    # 6. Planner ranking returns safe empty response
    res_plan_reg = client.get(
        "/planner/rankings?scope=region",
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert res_plan_reg.status_code == 200
    assert res_plan_reg.json()["total_areas_evaluated"] == 0
    assert res_plan_reg.json()["rankings"] == []
