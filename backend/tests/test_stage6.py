"""
Stage 6 Verification Tests — Map & Core Dashboard Backend.
Verifies:
1. Map / Locality APIs (/areas, /areas/{id})
2. Service APIs (/services, /services/{id}, /services/categories)
3. GeoJSON validation (/areas/geojson, /areas/{id}/geojson, /services/geojson)
4. Accessibility & Gap analytics APIs (/analytics/areas, /analytics/deserts)
5. Underserved Ranking API (/analytics/rankings/underserved)
6. Selected-area dashboard metrics (complete fields for UI scorecard)
7. Empty-data handling & edge cases
8. Backend startup & health
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_stage6_backend_startup():
    """Check 10: Backend starts successfully and health check probe passes."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_stage6_map_locality_api():
    """Check 1: Map / locality APIs work and return expected administrative areas."""
    # List areas
    res = client.get("/areas")
    assert res.status_code == 200
    areas = res.json()
    assert isinstance(areas, list)
    assert len(areas) >= 5

    # Filter by area_type
    res_wards = client.get("/areas?area_type=ward")
    assert res_wards.status_code == 200
    wards = res_wards.json()
    assert len(wards) >= 1
    assert all(w["area_type"] == "ward" for w in wards)

    # Specific area lookup
    area_id = areas[0]["id"]
    res_single = client.get(f"/areas/{area_id}")
    assert res_single.status_code == 200
    area_detail = res_single.json()
    assert area_detail["id"] == area_id
    assert "name" in area_detail
    assert "population" in area_detail


def test_stage6_service_api():
    """Check 2: Service API works, supports category list, filtering, and facility lookup."""
    # Service categories
    res_cats = client.get("/services/categories")
    assert res_cats.status_code == 200
    cats = res_cats.json()
    assert len(cats) >= 5
    cat_codes = [c["code"] for c in cats]
    for expected in ["healthcare", "education", "transport", "water", "market"]:
        assert expected in cat_codes

    # List services with category filter
    res_srv = client.get("/services?category_code=healthcare")
    assert res_srv.status_code == 200
    srvs = res_srv.json()
    assert len(srvs) >= 2
    assert all(s["category_code"] == "healthcare" for s in srvs)

    # Facility detail
    srv_id = srvs[0]["id"]
    res_srv_detail = client.get(f"/services/{srv_id}")
    assert res_srv_detail.status_code == 200
    srv_detail = res_srv_detail.json()
    assert srv_detail["id"] == srv_id
    assert "latitude" in srv_detail
    assert "longitude" in srv_detail
    assert "status" in srv_detail


def test_stage6_geojson_validation():
    """Check 3: GeoJSON validation for locality boundaries and service facility points."""
    # 1. Locality FeatureCollection GeoJSON
    res_areas_geo = client.get("/areas/geojson")
    assert res_areas_geo.status_code == 200
    fc = res_areas_geo.json()
    assert fc["type"] == "FeatureCollection"
    assert "features" in fc
    assert isinstance(fc["features"], list)
    assert len(fc["features"]) >= 5

    # Check first feature structure RFC 7946 compliance
    first_feat = fc["features"][0]
    assert first_feat["type"] == "Feature"
    assert "id" in first_feat
    assert "geometry" in first_feat
    assert first_feat["geometry"]["type"] in ["Polygon", "MultiPolygon"]
    assert "coordinates" in first_feat["geometry"]
    assert "properties" in first_feat
    assert "accessibility_score" in first_feat["properties"]
    assert "gap_score" in first_feat["properties"]
    assert "desert_classification" in first_feat["properties"]

    # 2. Single area GeoJSON feature
    area_id = first_feat["id"]
    res_single_geo = client.get(f"/areas/{area_id}/geojson")
    assert res_single_geo.status_code == 200
    single_feat = res_single_geo.json()
    assert single_feat["type"] == "Feature"
    assert single_feat["id"] == area_id
    assert single_feat["geometry"]["type"] in ["Polygon", "MultiPolygon"]

    # 3. Services Point FeatureCollection GeoJSON
    res_srv_geo = client.get("/services/geojson?category_code=healthcare")
    assert res_srv_geo.status_code == 200
    srv_fc = res_srv_geo.json()
    assert srv_fc["type"] == "FeatureCollection"
    assert len(srv_fc["features"]) >= 2

    first_srv_feat = srv_fc["features"][0]
    assert first_srv_feat["type"] == "Feature"
    assert first_srv_feat["geometry"]["type"] == "Point"
    # GeoJSON coordinates order: [longitude, latitude]
    coords = first_srv_feat["geometry"]["coordinates"]
    assert len(coords) == 2
    assert -180.0 <= coords[0] <= 180.0  # longitude
    assert -90.0 <= coords[1] <= 90.0   # latitude
    assert first_srv_feat["properties"]["category_code"] == "healthcare"


def test_stage6_accessibility_gap_api():
    """Check 4: Accessibility and gap analytics endpoints return verified metrics."""
    # Areas analytics list
    res_analytics = client.get("/analytics/areas")
    assert res_analytics.status_code == 200
    data = res_analytics.json()
    assert len(data) >= 5
    for item in data:
        assert 0.0 <= item["composite_accessibility_score"] <= 100.0
        assert 0.0 <= item["composite_gap_score"] <= 100.0
        assert round(item["composite_accessibility_score"] + item["composite_gap_score"], 1) == 100.0

    # Service deserts list
    res_deserts = client.get("/analytics/deserts")
    assert res_deserts.status_code == 200
    deserts = res_deserts.json()
    assert isinstance(deserts, list)
    assert len(deserts) > 0
    # Highlands Valley / Vijay Nagar healthcare desert is present
    desert_area_names = [d["area_name"] for d in deserts if d["category_code"] == "healthcare"]
    assert any(name in desert_area_names for name in ["Vijay Nagar", "Highlands Valley"])


def test_stage6_ranking_api():
    """Check 5: Underserved ranking API returns prioritized leaderboard."""
    # Composite ranking
    res_comp_rank = client.get("/analytics/rankings/underserved?limit=5")
    assert res_comp_rank.status_code == 200
    comp_rank = res_comp_rank.json()
    assert comp_rank["category_evaluated"] == "composite"
    assert comp_rank["total_areas_evaluated"] >= 5
    assert len(comp_rank["rankings"]) <= 5
    assert comp_rank["rankings"][0]["rank"] == 1
    # Check descending gap order
    gaps = [r["gap_score"] for r in comp_rank["rankings"]]
    assert gaps == sorted(gaps, reverse=True)

    # Category-specific ranking for healthcare
    res_cat_rank = client.get("/analytics/rankings/underserved?category_code=healthcare&limit=5")
    assert res_cat_rank.status_code == 200
    cat_rank = res_cat_rank.json()
    assert cat_rank["category_evaluated"] == "healthcare"
    assert len(cat_rank["rankings"]) > 0
    # Highlands Valley / Vijay Nagar has 0 healthcare facilities, so it should rank #1 in healthcare need
    assert cat_rank["rankings"][0]["area_name"] in ["Vijay Nagar", "Highlands Valley"]
    assert cat_rank["rankings"][0]["rank"] == 1


def test_stage6_selected_area_metrics():
    """Check 6: Selected-area analytics provides all required Core Dashboard scorecard fields."""
    # Look up Highlands Valley (area_id = 9)
    res = client.get("/analytics/areas/9")
    assert res.status_code == 200
    data = res.json()

    # Core Dashboard Required Fields:
    # 1. Accessibility Score
    assert "composite_accessibility_score" in data
    # 2. Gap Score
    assert "composite_gap_score" in data
    # 3. Service Desert Classification
    assert "composite_desert_classification" in data
    # 4. Population
    assert data["population"] == 22000

    # 5. Category Breakdown with nearest service, travel time, capacity, equity, confidence, reality gap
    assert "category_breakdown" in data
    breakdown = data["category_breakdown"]
    assert len(breakdown) == 5

    healthcare_cat = next(c for c in breakdown if c["category_code"] == "healthcare")
    assert "nearest_service_name" in healthcare_cat
    assert "travel_time_minutes" in healthcare_cat
    assert "travel_time_score" in healthcare_cat
    assert "service_pressure" in healthcare_cat
    assert "capacity_score" in healthcare_cat["service_pressure"]
    assert "pressure_category" in healthcare_cat["service_pressure"]
    assert "equity_score" in healthcare_cat
    assert "confidence_score" in healthcare_cat
    assert "reality_gap_score" in healthcare_cat
    assert "reality_gap_level" in healthcare_cat
    assert "reality_gap_summary" in healthcare_cat


def test_stage6_empty_data_handling():
    """Check 7: Empty-data handling and boundary filters without exceptions or malformed JSON."""
    # Filter with nonexistent category
    res_bad_cat = client.get("/services?category_code=nonexistent_category")
    assert res_bad_cat.status_code == 200
    assert res_bad_cat.json() == []

    # Nonexistent status filter
    res_bad_status = client.get("/services?status=nonexistent_status")
    assert res_bad_status.status_code == 200
    assert res_bad_status.json() == []

    # Nonexistent area filter
    res_bad_area = client.get("/services?area_id=99999")
    assert res_bad_status.status_code == 200
    assert res_bad_status.json() == []

    # Empty GeoJSON
    res_empty_geo = client.get("/services/geojson?category_code=nonexistent_category")
    assert res_empty_geo.status_code == 200
    empty_fc = res_empty_geo.json()
    assert empty_fc["type"] == "FeatureCollection"
    assert empty_fc["features"] == []

    # Invalid area ID returns clean 404
    res_404_area = client.get("/areas/99999")
    assert res_404_area.status_code == 404
    assert res_404_area.json()["status_code"] == 404

    res_404_area_geo = client.get("/areas/99999/geojson")
    assert res_404_area_geo.status_code == 404
    assert res_404_area_geo.json()["status_code"] == 404
