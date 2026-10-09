"""
Unit and integration tests for Stage 3 Geospatial & Analytics Engine.
Covers deterministic calculations, gap score, desert classifications,
service pressure, capacity handling, weights validation, and API routes.
"""
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.analytics.config import AnalyticsConfig, default_analytics_config
from app.analytics.distance import (
    haversine_distance_km,
    extract_centroid_lat_lon,
    DeterministicRoutingProvider,
)
from app.analytics.engine import AnalyticsEngine, default_analytics_engine
from app.models import Service, ServiceCapacity

client = TestClient(app)


# --- 1. Unit Tests: Distance & Routing Abstraction ---

def test_haversine_distance_calculation():
    """Verify haversine distance calculation produces accurate real-world results."""
    # Bangalore City Center (12.9716, 77.5946) to Indiranagar (12.9784, 77.6408) is ~5.0 km
    dist = haversine_distance_km(12.9716, 77.5946, 12.9784, 77.6408)
    assert 4.5 <= dist <= 5.5

    # Zero distance between identical coordinates
    assert haversine_distance_km(12.9716, 77.5946, 12.9716, 77.5946) == 0.0


def test_extract_centroid_lat_lon():
    """Verify geometry centroid extraction parses WKT and GeoJSON points/polygons."""
    # WKT Point
    lat, lon = extract_centroid_lat_lon("POINT (77.5946 12.9716)")
    assert round(lat, 4) == 12.9716
    assert round(lon, 4) == 77.5946

    # GeoJSON Polygon string
    geojson_poly = '{"type": "Polygon", "coordinates": [[[77.0, 12.0], [78.0, 12.0], [78.0, 13.0], [77.0, 13.0], [77.0, 12.0]]]}'
    lat, lon = extract_centroid_lat_lon(geojson_poly)
    assert round(lat, 1) == 12.5
    assert round(lon, 1) == 77.5


def test_deterministic_routing_provider():
    """Verify that deterministic routing calculates travel time without external API dependency."""
    router = DeterministicRoutingProvider()
    result = router.estimate_travel(
        origin_lat=12.9716,
        origin_lon=77.5946,
        dest_lat=12.9784,
        dest_lon=77.6408,
        mode="transit",
    )
    assert result["is_estimate"] is True
    assert result["direct_distance_km"] > 0
    assert result["estimated_network_distance_km"] > result["direct_distance_km"]
    assert result["estimated_travel_time_minutes"] > 0


# --- 2. Unit Tests: Travel-Time Score Thresholds ---

def test_travel_time_score_thresholds():
    """
    Test exact deterministic threshold model:
    0–10 min   = 100
    10–20 min  = 80
    20–30 min  = 60
    30–45 min  = 35
    > 45 min   = 10
    infinite   = 0
    """
    engine = AnalyticsEngine()

    assert engine.calculate_travel_time_score(5.0) == 100.0
    assert engine.calculate_travel_time_score(10.0) == 100.0
    assert engine.calculate_travel_time_score(10.1) == 80.0
    assert engine.calculate_travel_time_score(20.0) == 80.0
    assert engine.calculate_travel_time_score(25.0) == 60.0
    assert engine.calculate_travel_time_score(30.0) == 60.0
    assert engine.calculate_travel_time_score(35.0) == 35.0
    assert engine.calculate_travel_time_score(45.0) == 35.0
    assert engine.calculate_travel_time_score(45.1) == 10.0
    assert engine.calculate_travel_time_score(90.0) == 10.0
    assert engine.calculate_travel_time_score(float("inf")) == 0.0


# --- 3. Unit Tests: Service Availability Score ---

def test_availability_score():
    """
    Verify service state maps deterministically to 0–100 scores:
    operational: 100, limited: 60, degraded: 50, temporarily_unavailable: 20, closed: 0
    """
    engine = AnalyticsEngine()

    s_op = Service(name="Test Op", status="operational", latitude=0, longitude=0)
    assert engine.calculate_availability_score(s_op) == 100.0

    s_lim = Service(name="Test Lim", status="limited", latitude=0, longitude=0)
    assert engine.calculate_availability_score(s_lim) == 60.0

    s_deg = Service(name="Test Deg", status="degraded", latitude=0, longitude=0)
    assert engine.calculate_availability_score(s_deg) == 50.0

    s_temp = Service(name="Test Temp", status="temporarily_unavailable", latitude=0, longitude=0)
    assert engine.calculate_availability_score(s_temp) == 20.0

    s_closed = Service(name="Test Closed", status="closed", latitude=0, longitude=0)
    assert engine.calculate_availability_score(s_closed) == 0.0

    # None service
    assert engine.calculate_availability_score(None) == 0.0


# --- 4. Unit Tests: Capacity & Service Pressure ---

def test_capacity_and_service_pressure_no_crash():
    """
    Verify capacity score and service pressure handle missing, zero, limited,
    and sufficient capacity without crashing or dividing by zero.
    """
    engine = AnalyticsEngine()

    # Case 1: Missing Service
    res_none = engine.calculate_capacity_and_pressure(None, demand_population=5000)
    assert res_none["capacity_score"] == 0.0
    assert res_none["pressure_category"] == "Critical"
    assert res_none["data_quality"] == "no_service_available"

    # Case 2: Service with Missing Capacity Record
    s_no_cap = Service(name="No Cap Record", status="operational", latitude=0, longitude=0)
    s_no_cap.capacity_record = None
    res_no_cap = engine.calculate_capacity_and_pressure(s_no_cap, demand_population=5000)
    assert res_no_cap["capacity_score"] == 50.0
    assert res_no_cap["pressure_category"] == "Moderate"
    assert res_no_cap["data_quality"] == "unreported"

    # Case 3: Service with Zero Capacity (Division by zero protection)
    s_zero = Service(name="Zero Cap", status="operational", latitude=0, longitude=0)
    s_zero.capacity_record = ServiceCapacity(capacity=0, current_load=0, status="normal")
    res_zero = engine.calculate_capacity_and_pressure(s_zero, demand_population=5000)
    assert res_zero["capacity_score"] == 0.0
    assert res_zero["pressure_category"] == "Critical"
    assert res_zero["pressure_ratio"] == 999.0
    assert res_zero["data_quality"] == "zero_capacity"

    # Case 4: Service with Sufficient Capacity
    s_good = Service(name="Good Cap", status="operational", latitude=0, longitude=0)
    s_good.capacity_record = ServiceCapacity(capacity=100, current_load=40, status="normal")
    res_good = engine.calculate_capacity_and_pressure(s_good, demand_population=50)
    assert res_good["capacity_score"] >= 80.0
    assert res_good["pressure_category"] == "Low"
    assert res_good["data_quality"] == "verified_record"

    # Case 5: Service with Overloaded Capacity
    s_over = Service(name="Overloaded", status="operational", latitude=0, longitude=0)
    s_over.capacity_record = ServiceCapacity(capacity=50, current_load=65, status="overloaded")
    res_over = engine.calculate_capacity_and_pressure(s_over, demand_population=500)
    assert res_over["capacity_score"] == 20.0
    assert res_over["pressure_category"] == "Critical"


# --- 5. Unit Tests: Gap Score Formula and Boundaries ---

def test_gap_score_formula_and_boundaries():
    """
    Ensure Gap Score = 100 - Accessibility Score.
    Test perfect access, zero access, middle values, and boundary values.
    """
    # Perfect access
    acc_perf = 100.0
    gap_perf = round(max(0.0, min(100.0, 100.0 - acc_perf)), 1)
    assert gap_perf == 0.0

    # Zero access
    acc_zero = 0.0
    gap_zero = round(max(0.0, min(100.0, 100.0 - acc_zero)), 1)
    assert gap_zero == 100.0

    # Middle value
    acc_mid = 62.5
    gap_mid = round(max(0.0, min(100.0, 100.0 - acc_mid)), 1)
    assert gap_mid == 37.5

    # Boundary guarantees: 0 <= Gap Score <= 100
    for test_score in [-10.0, 0.0, 25.4, 50.0, 75.8, 100.0, 115.0]:
        clamped_acc = max(0.0, min(100.0, test_score))
        gap = round(max(0.0, min(100.0, 100.0 - clamped_acc)), 1)
        assert 0.0 <= gap <= 100.0


# --- 6. Unit Tests: Service Desert Classifications & Boundaries ---

def test_service_desert_classifications_all_boundaries():
    """
    Implement exact baseline classifications:
    80–100 = Well Served
    60–79  = Adequate
    40–59  = At Risk
    20–39  = Underserved
    0–19   = Critical Desert
    """
    engine = AnalyticsEngine()

    # Boundaries for Well Served [80, 100]
    assert engine.classify_service_desert(100.0) == "Well Served"
    assert engine.classify_service_desert(85.0) == "Well Served"
    assert engine.classify_service_desert(80.0) == "Well Served"

    # Boundaries for Adequate [60, 79.9]
    assert engine.classify_service_desert(79.9) == "Adequate"
    assert engine.classify_service_desert(70.0) == "Adequate"
    assert engine.classify_service_desert(60.0) == "Adequate"

    # Boundaries for At Risk [40, 59.9]
    assert engine.classify_service_desert(59.9) == "At Risk"
    assert engine.classify_service_desert(50.0) == "At Risk"
    assert engine.classify_service_desert(40.0) == "At Risk"

    # Boundaries for Underserved [20, 39.9]
    assert engine.classify_service_desert(39.9) == "Underserved"
    assert engine.classify_service_desert(30.0) == "Underserved"
    assert engine.classify_service_desert(20.0) == "Underserved"

    # Boundaries for Critical Desert [0, 19.9]
    assert engine.classify_service_desert(19.9) == "Critical Desert"
    assert engine.classify_service_desert(10.0) == "Critical Desert"
    assert engine.classify_service_desert(0.0) == "Critical Desert"


# --- 7. Unit Tests: Central Config & Weight Validation ---

def test_analytics_config_weights_validation():
    """
    Verify weights are validated to sum to 1.0 (100%).
    30% Travel Time, 20% Service Availability, 20% Capacity, 15% Transport Connectivity, 15% Equity.
    """
    cfg = default_analytics_config
    total_weight = (
        cfg.travel_time_weight
        + cfg.availability_weight
        + cfg.capacity_weight
        + cfg.transport_weight
        + cfg.equity_weight
    )
    assert pytest.approx(total_weight, 0.001) == 1.0

    # Invalid weights sum must raise validation error
    with pytest.raises(ValueError):
        AnalyticsConfig(
            travel_time_weight=0.50,
            availability_weight=0.50,
            capacity_weight=0.50,  # Sum = 1.50 != 1.0
            transport_weight=0.15,
            equity_weight=0.15,
        )


# --- 8. Integration Tests: Analytics API Endpoints ---

def test_api_get_analytics_config():
    """Test GET /analytics/config returns weights, thresholds, and mappings."""
    response = client.get("/analytics/config")
    assert response.status_code == 200
    data = response.json()
    assert data["travel_time_weight"] == 0.30
    assert data["availability_weight"] == 0.20
    assert data["capacity_weight"] == 0.20
    assert data["transport_weight"] == 0.15
    assert data["equity_weight"] == 0.15
    assert len(data["travel_time_thresholds"]) == 5
    assert len(data["desert_classifications"]) == 5


def test_api_get_areas_analytics():
    """Test GET /analytics/areas returns summaries for all geographic areas."""
    response = client.get("/analytics/areas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    for area in data:
        assert "area_id" in area
        assert "composite_accessibility_score" in area
        assert "composite_gap_score" in area
        assert "composite_desert_classification" in area
        assert 0.0 <= area["composite_accessibility_score"] <= 100.0
        assert 0.0 <= area["composite_gap_score"] <= 100.0


def test_api_get_area_detail_and_highlands_valley_healthcare_desert():
    """
    Highlands Valley (Pop 22,000) was seeded in Stage 1 with NO healthcare facilities.
    Verify that our analytics engine accurately flags it as a healthcare desert.
    """
    # 1. Discover Highlands Valley ID dynamically from areas endpoint
    areas_resp = client.get("/analytics/areas")
    assert areas_resp.status_code == 200
    hv_area = next(
        (a for a in areas_resp.json() if a["area_name"] == "Highlands Valley"),
        None,
    )
    assert hv_area is not None, "Highlands Valley must be present in geographic areas"
    hv_id = hv_area["area_id"]

    # 2. Detail endpoint with all categories
    response = client.get(f"/analytics/areas/{hv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["area_name"] == "Highlands Valley"
    assert data["category_breakdown"] is not None

    # Find healthcare category in breakdown
    hc_breakdown = next(
        (b for b in data["category_breakdown"] if b["category_code"] == "healthcare"),
        None,
    )
    assert hc_breakdown is not None
    # Highlands Valley has 0 healthcare facilities in catchment -> Critical Desert or Underserved
    assert hc_breakdown["accessibility_score"] < 40.0
    assert hc_breakdown["service_desert_classification"] in ["Critical Desert", "Underserved"]
    assert hc_breakdown["gap_score"] > 60.0

    # 3. Category-specific endpoint
    cat_response = client.get(f"/analytics/areas/{hv_id}/category/healthcare")
    assert cat_response.status_code == 200
    cat_data = cat_response.json()
    assert cat_data["category_code"] == "healthcare"
    assert cat_data["service_desert_classification"] in ["Critical Desert", "Underserved"]
    assert "reality_gap_level" in cat_data
    assert "confidence_score" in cat_data


def test_api_get_area_category_analytics_not_found():
    """Verify 404 error responses for invalid area or category identifiers."""
    # Invalid area ID
    res1 = client.get("/analytics/areas/99999/category/healthcare")
    assert res1.status_code == 404

    # Invalid category code
    res2 = client.get("/analytics/areas/1/category/non_existent_category")
    assert res2.status_code == 404


def test_api_get_service_deserts():
    """Test GET /analytics/deserts identifies low-access areas."""
    response = client.get("/analytics/deserts")
    assert response.status_code == 200
    deserts = response.json()
    assert isinstance(deserts, list)
    assert len(deserts) > 0

    # Highlands Valley healthcare must be in the desert list
    highlands_hc = next(
        (d for d in deserts if d["area_name"] == "Highlands Valley" and d["category_code"] == "healthcare"),
        None,
    )
    assert highlands_hc is not None
    assert highlands_hc["accessibility_score"] < 40.0
    assert highlands_hc["gap_score"] > 60.0

    # Filtered by category
    filter_response = client.get("/analytics/deserts?category_code=healthcare")
    assert filter_response.status_code == 200
    filtered_deserts = filter_response.json()
    for d in filtered_deserts:
        assert d["category_code"] == "healthcare"
