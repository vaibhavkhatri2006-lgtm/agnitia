"""
Tests for CivicPulse Real Data Mode, OpenStreetMap (Overpass API) integration,
Operational Mode toggling, Provenance tracking, OSRM routing with fallback,
Coordinate validation, Deduplication, and Population integrity.
All tests run fully offline without external API dependencies.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Service, GeographicArea, AuditLog, ServiceCategory
from app.analytics.distance import OSRMRoutingProvider, DeterministicRoutingProvider
from app.services.mode_service import get_current_mode, set_current_mode
from app.services.osm_service import (
    build_overpass_query,
    validate_coordinates,
    check_is_duplicate,
    import_osm_locality_data,
    clear_osm_cache,
    get_cache_stats,
    OSM_CATEGORY_TAGS,
)
from app.schemas.real_data import OSMImportRequest

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provides a database session for test execution."""
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True, scope="module")
def cleanup_osm_test_records_module():
    """Ensures database is clean of imported non-demo services before and after test module."""
    from app.database import SessionLocal
    def _clean():
        session = SessionLocal()
        try:
            session.query(AuditLog).filter(AuditLog.actor_id == "osm_importer").delete()
            session.query(Service).filter(Service.source_type != "simulated_demo").delete()
            session.commit()
        finally:
            session.close()

    _clean()
    yield
    _clean()


@pytest.fixture(autouse=True)
def cleanup_osm_test_records_function():
    """Cleans up imported non-demo services after each test."""
    from app.database import SessionLocal
    yield
    session = SessionLocal()
    try:
        session.query(AuditLog).filter(AuditLog.actor_id == "osm_importer").delete()
        session.query(Service).filter(Service.source_type != "simulated_demo").delete()
        session.commit()
    finally:
        session.close()


# --- Mock Overpass Elements for Ingestion Testing ---
MOCK_OVERPASS_PAYLOAD = {
    "version": 0.6,
    "generator": "Overpass API (Mock)",
    "elements": [
        # Valid Clinic (Healthcare)
        {
            "type": "node",
            "id": 1001,
            "lat": 12.9341,
            "lon": 77.6152,
            "tags": {
                "amenity": "clinic",
                "name": "Koramangala Community Health Center",
                "opening_hours": "08:00-20:00",
            },
        },
        # Valid Hospital (Healthcare)
        {
            "type": "node",
            "id": 1002,
            "lat": 12.9380,
            "lon": 77.6200,
            "tags": {
                "amenity": "hospital",
                "name": "Apex City Hospital",
            },
        },
        # Valid School (Education)
        {
            "type": "node",
            "id": 1003,
            "lat": 12.9310,
            "lon": 77.6120,
            "tags": {
                "amenity": "school",
                "name": "National Public School",
            },
        },
        # Valid Bus Stop (Transport)
        {
            "type": "node",
            "id": 1004,
            "lat": 12.9355,
            "lon": 77.6175,
            "tags": {
                "highway": "bus_stop",
                "name": "Koramangala BDA Complex Stop",
            },
        },
        # Valid Water Point (Water)
        {
            "type": "node",
            "id": 1005,
            "lat": 12.9360,
            "lon": 77.6180,
            "tags": {
                "amenity": "drinking_water",
                "name": "Municipal RO Water Kiosk",
            },
        },
        # Valid Market (Market)
        {
            "type": "node",
            "id": 1006,
            "lat": 12.9370,
            "lon": 77.6190,
            "tags": {
                "amenity": "marketplace",
                "name": "Koramangala Daily Farmers Market",
            },
        },
        # Duplicate facility (within 5 meters of Hospital 1002, same category)
        {
            "type": "node",
            "id": 1007,
            "lat": 12.93802,
            "lon": 77.62002,
            "tags": {
                "amenity": "hospital",
                "name": "Apex City Hospital (Duplicate Entry)",
            },
        },
        # Element with Invalid Coordinates (out of range latitude 99.0)
        {
            "type": "node",
            "id": 1008,
            "lat": 99.0,
            "lon": 77.6152,
            "tags": {
                "amenity": "clinic",
                "name": "Invalid Geo Clinic",
            },
        },
        # Element with Null Island Coordinates (0.0, 0.0)
        {
            "type": "node",
            "id": 1009,
            "lat": 0.0,
            "lon": 0.0,
            "tags": {
                "amenity": "school",
                "name": "Null Island Academy",
            },
        },
    ],
}


class TestCivicPulseModeSwitching:
    """Tests operational mode inspection and toggle between Demo and Real Data modes."""

    def test_get_operational_mode_default(self):
        # Reset to demo
        set_current_mode("demo")
        resp = client.get("/mode")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "demo"
        assert data["demo_available"] is True
        assert data["real_available"] is True
        assert "simulated_demo" in data["active_sources"]
        assert "DEMO MODE" in data["description"]

    def test_switch_to_real_data_mode(self):
        resp = client.post("/mode", json={"mode": "real"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "real"
        assert "osm" in data["active_sources"]
        assert "REAL DATA MODE" in data["description"]
        assert get_current_mode() == "real"

    def test_switch_mode_invalid_value(self):
        resp = client.post("/mode", json={"mode": "unsupported_hybrid"})
        assert resp.status_code == 400
        assert "Invalid mode" in resp.json()["detail"]

    def test_switch_back_to_demo_mode(self):
        resp = client.post("/mode", json={"mode": "demo"})
        assert resp.status_code == 200
        assert resp.json()["mode"] == "demo"
        assert get_current_mode() == "demo"


class TestOverpassQueryBuilder:
    """Tests generation of Overpass QL queries for all required civic infrastructure categories."""

    def test_all_five_categories_supported(self):
        required_categories = {"healthcare", "education", "transport", "water", "market"}
        assert required_categories.issubset(set(OSM_CATEGORY_TAGS.keys()))

    def test_build_query_with_bounding_box(self):
        bbox = [12.925, 77.610, 12.945, 77.635]
        query = build_overpass_query(
            categories=["healthcare", "education", "water"],
            bbox=bbox,
            timeout_seconds=30,
        )
        assert "[out:json][timeout:30];" in query
        assert "(12.925,77.61,12.945,77.635)" in query
        assert 'node["amenity"="hospital"]' in query
        assert 'node["amenity"="school"]' in query
        assert 'node["amenity"="drinking_water"]' in query
        assert "out center;" in query

    def test_build_query_with_center_and_radius(self):
        query = build_overpass_query(
            categories=["transport", "market"],
            center_lat=12.9716,
            center_lon=77.5946,
            radius_meters=1500,
        )
        assert "(around:1500,12.9716,77.5946)" in query
        assert 'node["highway"="bus_stop"]' in query
        assert 'node["amenity"="marketplace"]' in query

    def test_preview_query_api_endpoint(self):
        resp = client.get("/osm/query", params={
            "center_lat": 12.935,
            "center_lon": 77.615,
            "radius_meters": 2000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "overpass_ql" in data
        assert "around:2000" in data["overpass_ql"]
        assert "overpass-api.de" in data["endpoint"]


class TestCoordinateValidationAndDeduplication:
    """Tests coordinate validation rules and spatial deduplication logic."""

    def test_coordinate_validation_rules(self):
        # Valid coordinates
        assert validate_coordinates(12.9716, 77.5946) is True
        assert validate_coordinates(-33.8688, 151.2093) is True
        assert validate_coordinates(0.1, 0.1) is True

        # Latitude out of range
        assert validate_coordinates(91.0, 77.0) is False
        assert validate_coordinates(-90.5, 77.0) is False

        # Longitude out of range
        assert validate_coordinates(12.0, 181.0) is False
        assert validate_coordinates(12.0, -185.0) is False

        # Null Island (0.0, 0.0)
        assert validate_coordinates(0.0, 0.0) is False

        # Non-numeric / None
        assert validate_coordinates(None, 77.0) is False
        assert validate_coordinates("invalid", 77.0) is False
        assert validate_coordinates(float("nan"), 77.0) is False

    def test_spatial_deduplication(self, db_session):
        category = db_session.query(ServiceCategory).filter_by(code="healthcare").first()
        assert category is not None

        # Existing facility at lat=12.9300, lon=77.6100
        batch_coords = [(12.9300, 77.6100, category.id)]

        # Point ~2 meters away in same category -> DUPLICATE
        assert check_is_duplicate(
            db_session,
            lat=12.93002,
            lon=77.61002,
            category_id=category.id,
            batch_imported_coords=batch_coords,
        ) is True

        # Point in different category at same location -> NOT duplicate
        other_cat_id = category.id + 999
        assert check_is_duplicate(
            db_session,
            lat=12.93002,
            lon=77.61002,
            category_id=other_cat_id,
            batch_imported_coords=batch_coords,
        ) is False

        # Point 1 km away in same category -> NOT duplicate
        assert check_is_duplicate(
            db_session,
            lat=12.9400,
            lon=77.6200,
            category_id=category.id,
            batch_imported_coords=batch_coords,
        ) is False


class TestOSMImportAndProvenance:
    """Tests end-to-end OSM ingestion, provenance storage, and population handling."""

    def test_import_with_mock_overpass_data(self, db_session):
        clear_osm_cache()
        # Clean up any previously imported OSM test records
        db_session.query(AuditLog).filter(AuditLog.actor_id == "osm_importer").delete()
        db_session.query(Service).filter(Service.source_type == "osm").delete()
        db_session.commit()

        req = OSMImportRequest(
            locality_name="Koramangala Ward Test",
            center_latitude=12.934,
            center_longitude=77.615,
            radius_meters=1500,
            documented_population=45000,
            population_source="Census 2021 Table B-12",
        )

        response = import_osm_locality_data(db_session, req, mock_data=MOCK_OVERPASS_PAYLOAD)

        assert response.status == "success"
        assert response.mode == "real"
        assert response.is_demo_data is False
        assert response.locality_name == "Koramangala Ward Test"

        summary = response.summary
        assert summary.total_osm_elements == 9
        # 6 valid distinct facilities (1 clinic, 1 hosp, 1 school, 1 bus stop, 1 water point, 1 market)
        assert summary.imported_count == 6
        # 1 duplicate (hospital 1007 within 5m of hospital 1002)
        assert summary.deduplicated_count == 1
        # 2 invalid coordinates (lat 99.0 and Null Island 0,0)
        assert summary.invalid_coordinates_count == 2
        assert summary.population_status == "documented"
        assert summary.population_count == 45000

        # Verify DB records
        imported_services = (
            db_session.query(Service)
            .filter(Service.source_type == "osm")
            .all()
        )
        assert len(imported_services) >= 6
        for svc in imported_services:
            assert svc.source_type == "osm"
            assert svc.confidence_score == 0.85
            assert svc.created_at is not None

        # Verify AuditLog provenance entries
        sample_svc = imported_services[0]
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.entity_type == "service")
            .filter(AuditLog.entity_id == sample_svc.id)
            .filter(AuditLog.action == "osm_import")
            .first()
        )
        assert audit is not None
        provenance = json.loads(audit.new_value)
        assert provenance["source"] == "OpenStreetMap"
        assert provenance["attribution"] == "© OpenStreetMap contributors"
        assert "retrieval_timestamp" in provenance
        assert provenance["is_demo_data"] is False
        assert "coordinates" in provenance

    def test_population_never_synthesized_when_missing(self, db_session):
        """Do not invent missing population data; mark as unavailable."""
        req = OSMImportRequest(
            locality_name="Unpopulated Remote Area",
            center_latitude=12.950,
            center_longitude=77.650,
            documented_population=None,  # No documented population provided
        )

        # Single clinic payload
        single_elem_payload = {
            "elements": [
                {
                    "type": "node",
                    "id": 9901,
                    "lat": 12.951,
                    "lon": 77.651,
                    "tags": {"amenity": "clinic", "name": "Remote Rural Clinic"},
                }
            ]
        }

        response = import_osm_locality_data(db_session, req, mock_data=single_elem_payload)
        assert response.summary.population_status == "unavailable"
        assert response.summary.population_count is None

    def test_service_provenance_api_endpoint(self, db_session):
        # Find any OSM service or create one
        cat = db_session.query(ServiceCategory).first()
        svc = Service(
            name="Test Provenance Dispensary",
            category_id=cat.id,
            latitude=12.9100,
            longitude=77.6000,
            geometry="POINT(77.6000 12.9100)",
            source_type="osm",
            confidence_score=0.85,
        )
        db_session.add(svc)
        db_session.flush()

        audit = AuditLog(
            actor_id="osm_importer",
            action="osm_import",
            entity_type="service",
            entity_id=svc.id,
            new_value=json.dumps({
                "osm_id": 55555,
                "source": "OpenStreetMap",
                "license": "ODbL 1.0",
                "retrieval_timestamp": "2026-10-09T00:00:00Z",
                "attribution": "© OpenStreetMap contributors",
            }),
        )
        db_session.add(audit)
        db_session.commit()

        # Test GET /osm/provenance/{service_id}
        resp = client.get(f"/osm/provenance/{svc.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service_id"] == svc.id
        assert data["source_type"] == "osm"
        assert data["is_demo_data"] is False
        assert data["license"] == "ODbL 1.0"

        # Test GET /services/{service_id}/provenance
        resp2 = client.get(f"/services/{svc.id}/provenance")
        assert resp2.status_code == 200
        assert resp2.json()["service_id"] == svc.id


class TestOSRMRoutingAndFallback:
    """Tests OSRM network routing integration with graceful fallback to deterministic approximation."""

    def test_osrm_unconfigured_uses_deterministic(self):
        provider = OSRMRoutingProvider(base_url=None)
        res = provider.estimate_travel(12.9716, 77.5946, 12.9352, 77.6245, mode="transit")
        assert res["provider"] == "deterministic_approximation"
        assert res["is_estimate"] is True
        assert res["estimated_travel_time_minutes"] > 0

    def test_osrm_network_failure_falls_back_gracefully(self):
        # Configure an unreachable base URL
        provider = OSRMRoutingProvider(
            base_url="http://127.0.0.1:9999",  # unreachable port
            timeout_seconds=0.1,  # fast timeout
            fallback_provider=DeterministicRoutingProvider(),
        )
        res = provider.estimate_travel(12.9716, 77.5946, 12.9352, 77.6245, mode="driving")

        # Must gracefully fall back without raising an unhandled exception
        assert res["provider"] == "fallback_deterministic"
        assert "provider_warning" in res
        assert res["is_estimate"] is True
        assert res["estimated_travel_time_minutes"] > 0

    def test_osrm_mock_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "code": "Ok",
            "routes": [{"duration": 720.0, "distance": 4200.0}],
        }

        with patch("httpx.Client.get", return_value=mock_resp):
            provider = OSRMRoutingProvider(base_url="http://mock-osrm:5000", timeout_seconds=1.0)
            res = provider.estimate_travel(12.9716, 77.5946, 12.9352, 77.6245, mode="driving")
            assert res["provider"] == "osrm"
            assert res["is_estimate"] is True
            assert res["estimated_travel_time_minutes"] == 12.0  # 720 / 60
            assert res["estimated_network_distance_km"] == 4.2   # 4200 / 1000


class TestOSMCacheTelemetry:
    """Tests Overpass query cache telemetry and cache clear endpoints."""

    def test_cache_stats_and_clear(self):
        clear_osm_cache()
        resp = client.get("/osm/cache/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["cache_entries"] == 0
        assert stats["rate_limit_cooldown_seconds"] >= 1.0
        assert "CivicPulse" in stats["user_agent"]

        clear_resp = client.post("/osm/cache/clear")
        assert clear_resp.status_code == 200
        assert clear_resp.json()["status"] == "success"


class TestServicesModeFilter:
    """Tests filtering services by operational mode (demo vs real)."""

    def test_services_mode_query_param(self, db_session):
        # Insert a temporary OSM service
        cat = db_session.query(ServiceCategory).first()
        temp_svc = Service(
            name="Temporary Real Mode Clinic",
            category_id=cat.id,
            latitude=12.930,
            longitude=77.610,
            geometry="POINT(77.610 12.930)",
            source_type="osm",
            confidence_score=0.85,
        )
        db_session.add(temp_svc)
        db_session.commit()

        # Demo mode returns simulated_demo
        resp_demo = client.get("/services", params={"mode": "demo"})
        assert resp_demo.status_code == 200
        for s in resp_demo.json():
            assert s["source_type"] == "simulated_demo"

        # Real mode returns non-demo services (e.g. osm)
        resp_real = client.get("/services", params={"mode": "real"})
        assert resp_real.status_code == 200
        assert len(resp_real.json()) >= 1
        for s in resp_real.json():
            assert s["source_type"] != "simulated_demo"

        # GeoJSON endpoint supports mode filter as well
        resp_geojson = client.get("/services/geojson", params={"mode": "demo"})
        assert resp_geojson.status_code == 200
        assert resp_geojson.json()["type"] == "FeatureCollection"


class TestNormalizedOSMDataProvider:
    """
    Tests Overpass data provider normalization, representative area coordinates,
    category mapping, missing field integrity, empty/timeout states, and attribution.
    """

    MOCK_AREAS_AND_POINTS_PAYLOAD = {
        "version": 0.6,
        "elements": [
            # 1. Point feature: Clinic with name
            {
                "type": "node",
                "id": 2001,
                "lat": 12.9340,
                "lon": 77.6150,
                "tags": {
                    "amenity": "clinic",
                    "name": "Apex Family Clinic",
                    "opening_hours": "09:00-18:00",
                },
            },
            # 2. Point feature: Doctors facility
            {
                "type": "node",
                "id": 2002,
                "lat": 12.9345,
                "lon": 77.6155,
                "tags": {
                    "amenity": "doctors",
                    "name": "Dr. Rao Orthopedic Care",
                },
            },
            # 3. Point feature: Bus stop WITHOUT name (must not invent name)
            {
                "type": "node",
                "id": 2003,
                "lat": 12.9350,
                "lon": 77.6160,
                "tags": {
                    "highway": "bus_stop",
                },
            },
            # 4. Area feature (way): School with center coordinates
            {
                "type": "way",
                "id": 2004,
                "center": {
                    "lat": 12.9370,
                    "lon": 77.6180,
                },
                "tags": {
                    "amenity": "school",
                    "name": "Greenwood High Campus",
                },
            },
            # 5. Area feature (way): College with center coordinates
            {
                "type": "way",
                "id": 2005,
                "center": {
                    "lat": 12.9385,
                    "lon": 77.6195,
                },
                "tags": {
                    "amenity": "college",
                    "name": "City Engineering College",
                },
            },
            # 6. Area feature (relation): University with center coordinates
            {
                "type": "relation",
                "id": 2006,
                "center": {
                    "lat": 12.9400,
                    "lon": 77.6210,
                },
                "tags": {
                    "amenity": "university",
                    "name": "State Metropolitan University",
                },
            },
        ],
    }

    def test_get_normalized_services_demo_mode(self):
        set_current_mode("demo")
        resp = client.get("/osm/services", params={"locality_name": "Highlands Valley"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "simulated_demo"
        assert data["is_demo_data"] is True
        assert data["status"] in ("success", "empty")
        assert "© OpenStreetMap contributors" in data["attribution"]

        # Validate schema of services
        for s in data["services"]:
            assert "osm_id" in s
            assert "name" in s
            assert "service_category" in s
            assert "latitude" in s
            assert "longitude" in s
            assert "tags" in s
            assert "source" in s
            assert s["is_demo_data"] is True

    def test_get_normalized_services_with_points_and_areas(self, db_session):
        from app.services.osm_service import fetch_normalized_osm_services

        resp = fetch_normalized_osm_services(
            db=db_session,
            locality_name="Test Locality",
            force_live=True,
            mock_data=self.MOCK_AREAS_AND_POINTS_PAYLOAD,
        )

        assert resp.status == "success"
        assert resp.source == "OpenStreetMap"
        assert resp.is_demo_data is False
        assert resp.count == 6
        assert resp.attribution == "© OpenStreetMap contributors"

        services_by_id = {s.osm_id: s for s in resp.services}

        # 1. Point clinic
        clinic = services_by_id[2001]
        assert clinic.name == "Apex Family Clinic"
        assert clinic.service_category == "healthcare"
        assert clinic.latitude == 12.9340
        assert clinic.longitude == 77.6150
        assert clinic.osm_type == "node"
        assert clinic.source == "OpenStreetMap"
        assert clinic.operating_status == "09:00-18:00"
        assert clinic.capacity is None

        # 2. Point doctors
        doc = services_by_id[2002]
        assert doc.name == "Dr. Rao Orthopedic Care"
        assert doc.service_category == "healthcare"
        assert doc.latitude == 12.9345

        # 3. Unnamed bus stop: Name MUST NOT be invented!
        bus = services_by_id[2003]
        assert bus.name is None  # Integrity: Do not invent missing service names
        assert bus.service_category == "transport"
        assert bus.latitude == 12.9350
        assert bus.longitude == 77.6160
        assert bus.capacity is None
        assert bus.operating_status is None

        # 4. Area feature (way school): Representative coordinates extracted from center
        school = services_by_id[2004]
        assert school.name == "Greenwood High Campus"
        assert school.service_category == "education"
        assert school.latitude == 12.9370
        assert school.longitude == 77.6180
        assert school.osm_type == "way"

        # 5. Area feature (way college)
        college = services_by_id[2005]
        assert college.name == "City Engineering College"
        assert college.service_category == "education"
        assert college.latitude == 12.9385
        assert college.osm_type == "way"

        # 6. Area feature (relation university)
        univ = services_by_id[2006]
        assert univ.name == "State Metropolitan University"
        assert univ.service_category == "education"
        assert univ.latitude == 12.9400
        assert univ.osm_type == "relation"

    def test_get_normalized_services_empty_state(self, db_session):
        from app.services.osm_service import fetch_normalized_osm_services

        resp = fetch_normalized_osm_services(
            db=db_session,
            locality_name="Empty Desert Area",
            force_live=True,
            mock_data={"elements": []},
        )
        assert resp.status == "empty"
        assert resp.count == 0
        assert resp.services == []
        assert resp.source == "OpenStreetMap"
        assert resp.is_demo_data is False

    def test_get_normalized_services_timeout_fallback(self, db_session):
        from app.services.osm_service import fetch_normalized_osm_services

        with patch("app.services.osm_service.fetch_overpass_data", side_effect=RuntimeError("Overpass query timed out after 25s")):
            # Fallback to demo
            resp = fetch_normalized_osm_services(
                db=db_session,
                locality_name="Timeout Locality",
                force_live=True,
                fallback_to_demo=True,
            )
            assert resp.status == "timeout"
            assert resp.is_demo_data is True
            assert resp.source == "simulated_demo"
            assert "communication issue" in resp.warning

            # Strict error without fallback
            with pytest.raises(RuntimeError) as exc_info:
                fetch_normalized_osm_services(
                    db=db_session,
                    locality_name="Timeout Locality",
                    force_live=True,
                    fallback_to_demo=False,
                )
            assert "Overpass provider failure" in str(exc_info.value)

