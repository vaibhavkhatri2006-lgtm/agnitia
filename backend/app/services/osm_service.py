"""
OpenStreetMap (OSM) Ingestion Service for CivicPulse Real Data Mode.
Handles Overpass API querying, TTL-based caching, rate-limiting adherence,
coordinate validation, spatial deduplication, provenance tracking, and
population-integrity checks without fabricating synthetic values.
"""
import hashlib
import json
import logging
import math
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.analytics.distance import haversine_distance_km
from app.models import (
    Service,
    ServiceCategory,
    GeographicArea,
    AuditLog,
    DataSource,
)
from app.schemas.real_data import OSMImportRequest, OSMImportSummary, OSMImportResponse

logger = logging.getLogger(__name__)

# Respectful rate limiting: minimum seconds between live Overpass API calls
RATE_LIMIT_COOLDOWN_SECONDS = 1.0
_last_live_call_timestamp: float = 0.0

# In-memory query cache: {query_hash: {"data": dict, "timestamp": float}}
_query_cache: Dict[str, Dict[str, Any]] = {}
_cache_stats = {
    "hits": 0,
    "misses": 0,
}

# Overpass QL Tag mapping for CivicPulse civic infrastructure categories
OSM_CATEGORY_TAGS = {
    "healthcare": [
        ('amenity', 'hospital'),
        ('amenity', 'clinic'),
        ('amenity', 'doctors'),
        ('amenity', 'pharmacy'),
        ('healthcare', 'hospital'),
        ('healthcare', 'clinic'),
        ('healthcare', 'centre'),
    ],
    "education": [
        ('amenity', 'school'),
        ('amenity', 'college'),
        ('amenity', 'kindergarten'),
        ('amenity', 'university'),
    ],
    "transport": [
        ('highway', 'bus_stop'),
        ('public_transport', 'stop_position'),
        ('public_transport', 'platform'),
        ('railway', 'station'),
        ('railway', 'halt'),
        ('amenity', 'bus_station'),
    ],
    "water": [
        ('amenity', 'drinking_water'),
        ('amenity', 'water_point'),
        ('man_made', 'water_tap'),
        ('man_made', 'water_well'),
        ('emergency', 'drinking_water'),
    ],
    "market": [
        ('amenity', 'marketplace'),
        ('shop', 'supermarket'),
        ('shop', 'convenience'),
        ('shop', 'greengrocer'),
        ('shop', 'general'),
    ],
}


def build_overpass_query(
    categories: Optional[List[str]] = None,
    bbox: Optional[List[float]] = None,
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None,
    radius_meters: float = 2000.0,
    timeout_seconds: int = 25,
) -> str:
    """
    Constructs an Overpass QL query string targeting selected civic facilities.
    Filters by either bounding box [south, west, north, east] or around:radius,lat,lon.
    """
    selected_cats = categories or list(OSM_CATEGORY_TAGS.keys())
    timeout = timeout_seconds or getattr(settings, "OVERPASS_TIMEOUT_SECONDS", 25)

    if bbox and len(bbox) == 4:
        geo_filter = f"({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})"
    elif center_lat is not None and center_lon is not None:
        geo_filter = f"(around:{int(radius_meters)},{center_lat},{center_lon})"
    else:
        # Default fallback area (Central Bengaluru coordinates)
        geo_filter = f"(around:{int(radius_meters)},12.9716,77.5946)"

    statements = []
    for cat in selected_cats:
        tags = OSM_CATEGORY_TAGS.get(cat.lower(), [])
        for key, val in tags:
            statements.append(f'  node["{key}"="{val}"]{geo_filter};')
            statements.append(f'  way["{key}"="{val}"]{geo_filter};')

    statements_joined = "\n".join(statements)
    query = f"""[out:json][timeout:{timeout}];
(
{statements_joined}
);
out center;"""
    return query


def _compute_query_hash(query: str) -> str:
    """Computes a SHA256 digest of the query string for caching."""
    return hashlib.sha256(query.strip().encode("utf-8")).hexdigest()


def get_cache_stats() -> Dict[str, Any]:
    """Returns telemetry for Overpass query cache and rate limit parameters."""
    return {
        "cache_entries": len(_query_cache),
        "cache_hits": _cache_stats["hits"],
        "cache_misses": _cache_stats["misses"],
        "rate_limit_cooldown_seconds": RATE_LIMIT_COOLDOWN_SECONDS,
        "user_agent": settings.OSM_USER_AGENT,
    }


def clear_osm_cache() -> int:
    """Flushes in-memory Overpass query cache. Returns number of purged entries."""
    count = len(_query_cache)
    _query_cache.clear()
    _cache_stats["hits"] = 0
    _cache_stats["misses"] = 0
    logger.info("Overpass query cache cleared (%d entries removed).", count)
    return count


def fetch_overpass_data(query: str, mock_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], bool]:
    """
    Executes Overpass API query with TTL caching and rate limiting.
    Returns (data_dict, was_cached).
    Allows passing mock_data for testing offline without internet access.
    """
    global _last_live_call_timestamp

    if mock_data is not None:
        return mock_data, False

    query_hash = _compute_query_hash(query)
    now = time.time()
    ttl_seconds = getattr(settings, "OSM_CACHE_TTL_HOURS", 24) * 3600

    # 1. Check TTL cache
    if query_hash in _query_cache:
        cached_entry = _query_cache[query_hash]
        if now - cached_entry["timestamp"] < ttl_seconds:
            _cache_stats["hits"] += 1
            logger.info("Serving Overpass query from cache (hash=%s).", query_hash[:10])
            return cached_entry["data"], True

    # 2. Enforce rate-limiting cooldown before live call
    elapsed_since_last_call = now - _last_live_call_timestamp
    if elapsed_since_last_call < RATE_LIMIT_COOLDOWN_SECONDS:
        sleep_needed = RATE_LIMIT_COOLDOWN_SECONDS - elapsed_since_last_call
        time.sleep(sleep_needed)

    # 3. Execute live HTTP query to Overpass API
    headers = {
        "User-Agent": settings.OSM_USER_AGENT,
        "Accept": "application/json",
    }
    timeout = getattr(settings, "OVERPASS_TIMEOUT_SECONDS", 25)

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(settings.OVERPASS_URL, data={"data": query}, headers=headers)
            _last_live_call_timestamp = time.time()
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.error("Overpass API query failed: %s", exc)
        raise RuntimeError(f"Overpass API communication failure: {exc}") from exc

    # 4. Store in cache
    _query_cache[query_hash] = {
        "data": data,
        "timestamp": time.time(),
    }
    _cache_stats["misses"] += 1
    return data, False


def validate_coordinates(lat: Any, lon: Any) -> bool:
    """
    Validates geographical coordinates:
    - Must be finite floats.
    - Latitude between -90 and 90.
    - Longitude between -180 and 180.
    - Rejects (0.0, 0.0) 'Null Island'.
    """
    if lat is None or lon is None:
        return False
    try:
        flat = float(lat)
        flon = float(lon)
    except (ValueError, TypeError):
        return False

    if not (math.isfinite(flat) and math.isfinite(flon)):
        return False

    if not (-90.0 <= flat <= 90.0 and -180.0 <= flon <= 180.0):
        return False

    # Disallow (0,0) as invalid placeholder
    if abs(flat) < 0.0001 and abs(flon) < 0.0001:
        return False

    return True


def determine_category_code(tags: Dict[str, str]) -> Optional[str]:
    """Matches OSM element tags to CivicPulse service category."""
    amenity = tags.get("amenity", "").lower()
    healthcare = tags.get("healthcare", "").lower()
    shop = tags.get("shop", "").lower()
    highway = tags.get("highway", "").lower()
    public_transport = tags.get("public_transport", "").lower()
    railway = tags.get("railway", "").lower()
    man_made = tags.get("man_made", "").lower()
    emergency = tags.get("emergency", "").lower()

    if amenity in ["hospital", "clinic", "doctors", "pharmacy"] or healthcare in ["hospital", "clinic", "centre"]:
        return "healthcare"
    if amenity in ["school", "college", "kindergarten", "university"]:
        return "education"
    if (
        highway == "bus_stop"
        or public_transport in ["stop_position", "platform"]
        or railway in ["station", "halt"]
        or amenity == "bus_station"
    ):
        return "transport"
    if (
        amenity in ["drinking_water", "water_point"]
        or man_made in ["water_tap", "water_well"]
        or emergency == "drinking_water"
    ):
        return "water"
    if (
        amenity == "marketplace"
        or shop in ["supermarket", "convenience", "greengrocer", "general"]
    ):
        return "market"
    return None


def extract_element_coords(element: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """Extracts latitude and longitude from an OSM element (node, way, or relation)."""
    elem_type = element.get("type")
    if elem_type == "node":
        return element.get("lat"), element.get("lon")
    elif "center" in element and isinstance(element["center"], dict):
        return element["center"].get("lat"), element["center"].get("lon")
    elif "bounds" in element and isinstance(element["bounds"], dict):
        b = element["bounds"]
        return (b.get("minlat", 0) + b.get("maxlat", 0)) / 2.0, (b.get("minlon", 0) + b.get("maxlon", 0)) / 2.0
    return None, None


def check_is_duplicate(
    db: Session,
    lat: float,
    lon: float,
    category_id: int,
    batch_imported_coords: List[Tuple[float, float, int]],
    proximity_threshold_km: float = 0.015,  # 15 meters
) -> bool:
    """
    Deduplicates facilities:
    Checks if a facility in the same category already exists within 15 meters,
    either in the current ingestion batch or in the persistent database.
    """
    # 1. Check against current batch
    for b_lat, b_lon, b_cat_id in batch_imported_coords:
        if b_cat_id == category_id:
            dist = haversine_distance_km(lat, lon, b_lat, b_lon)
            if dist < proximity_threshold_km:
                return True

    # 2. Check against persistent database
    existing_services = db.query(Service).filter(Service.category_id == category_id).all()
    for s in existing_services:
        dist = haversine_distance_km(lat, lon, s.latitude, s.longitude)
        if dist < proximity_threshold_km:
            return True

    return False


def import_osm_locality_data(
    db: Session,
    request: OSMImportRequest,
    mock_data: Optional[Dict[str, Any]] = None,
) -> OSMImportResponse:
    """
    Main ingestion orchestrator for Real Data Mode:
    1. Resolves locality coordinates / geographic area.
    2. Builds Overpass query for clinics, hospitals, schools, transport stops, water points, and markets.
    3. Fetches data with rate-limiting & caching.
    4. Validates coordinates.
    5. Deduplicates services.
    6. Persists services with source='osm' and full provenance in AuditLog.
    7. Applies documented public population if supplied, or marks as unavailable.
    """
    # 1. Resolve Geographic Area
    area: Optional[GeographicArea] = None
    if request.area_id:
        area = db.query(GeographicArea).filter(GeographicArea.id == request.area_id).first()
    elif request.locality_name:
        area = db.query(GeographicArea).filter(GeographicArea.name.ilike(request.locality_name.strip())).first()

    # Determine query geographical bounds
    bbox = request.bbox
    center_lat = request.center_latitude
    center_lon = request.center_longitude
    radius = request.radius_meters or 2000.0

    if area and not bbox and center_lat is None:
        # Extract centroid or coordinates from area
        from app.analytics.distance import extract_centroid_lat_lon
        if area.geometry:
            try:
                center_lat, center_lon = extract_centroid_lat_lon(area.geometry)
            except Exception:
                center_lat, center_lon = 12.9716, 77.5946
        else:
            center_lat, center_lon = 12.9716, 77.5946

    # 2. Handle Population Integrity (Do NOT invent missing population)
    population_status = "unavailable"
    population_count = None

    if request.documented_population is not None:
        population_status = "documented"
        population_count = request.documented_population
        if area:
            area.population = request.documented_population
            db.flush()
    elif area and area.population and area.population > 0:
        # Area has an established official baseline population
        population_status = "official_census"
        population_count = area.population
    else:
        population_status = "unavailable"
        population_count = None

    # 3. Build & Fetch Overpass Query
    query = build_overpass_query(
        categories=request.categories,
        bbox=bbox,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_meters=radius,
        timeout_seconds=getattr(settings, "OVERPASS_TIMEOUT_SECONDS", 25),
    )

    data, was_cached = fetch_overpass_data(query, mock_data=mock_data)
    elements = data.get("elements", [])
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()

    # Ensure OSM data source is registered
    osm_source = db.query(DataSource).filter_by(code="osm").first()
    if not osm_source:
        osm_source = DataSource(
            code="osm",
            name="OpenStreetMap",
            description="Community geospatial data retrieved via Overpass API",
            trust_level=0.85,
            is_active=True,
        )
        db.add(osm_source)
        db.flush()

    # Fetch Category mapping
    categories_db = {c.code: c for c in db.query(ServiceCategory).all()}

    # 4. Process elements with coordinate validation and deduplication
    total_elements = len(elements)
    imported_count = 0
    dedup_count = 0
    invalid_coord_count = 0
    cat_counts: Dict[str, int] = {c: 0 for c in OSM_CATEGORY_TAGS.keys()}
    batch_coords: List[Tuple[float, float, int]] = []

    for elem in elements:
        raw_lat, raw_lon = extract_element_coords(elem)
        if not validate_coordinates(raw_lat, raw_lon):
            invalid_coord_count += 1
            continue

        lat = float(raw_lat)
        lon = float(raw_lon)

        tags = elem.get("tags", {})
        cat_code = determine_category_code(tags)
        if not cat_code or cat_code not in categories_db:
            continue

        cat_obj = categories_db[cat_code]

        # Check deduplication
        if check_is_duplicate(db, lat, lon, cat_obj.id, batch_coords):
            dedup_count += 1
            continue

        # Extract or format facility name
        name = tags.get("name") or tags.get("operator")
        if not name:
            name = f"OSM {cat_code.capitalize()} Facility ({elem.get('id')})"

        # Persist new Service
        new_svc = Service(
            name=name[:200],
            category_id=cat_obj.id,
            area_id=area.id if area else None,
            latitude=lat,
            longitude=lon,
            geometry=f"POINT({lon} {lat})",
            status="operational",
            source_type="osm",
            verification_status="unverified",
            confidence_score=0.85,
            operating_hours=tags.get("opening_hours"),
        )
        db.add(new_svc)
        db.flush()  # assign new_svc.id

        # Record provenance in AuditLog
        provenance_dict = {
            "osm_id": elem.get("id"),
            "osm_type": elem.get("type"),
            "osm_tags": tags,
            "source": "OpenStreetMap",
            "license": "ODbL 1.0 (Open Database Commons Open Database License)",
            "attribution": "© OpenStreetMap contributors",
            "retrieval_timestamp": retrieval_timestamp,
            "query_endpoint": settings.OVERPASS_URL,
            "category": cat_code,
            "coordinates": {"latitude": lat, "longitude": lon},
            "is_demo_data": False,
        }

        audit = AuditLog(
            actor_id="osm_importer",
            action="osm_import",
            entity_type="service",
            entity_id=new_svc.id,
            new_value=json.dumps(provenance_dict),
            reason=f"Imported from OpenStreetMap Overpass query for locality '{request.locality_name or (area.name if area else 'Custom Area')}'",
        )
        db.add(audit)

        batch_coords.append((lat, lon, cat_obj.id))
        imported_count += 1
        cat_counts[cat_code] = cat_counts.get(cat_code, 0) + 1

    # Record batch-level audit log
    batch_metadata = {
        "locality_name": request.locality_name or (area.name if area else "Custom Locality"),
        "area_id": area.id if area else None,
        "total_osm_elements": total_elements,
        "imported_services": imported_count,
        "deduplicated_services": dedup_count,
        "invalid_coordinates": invalid_coord_count,
        "categories_breakdown": cat_counts,
        "cached": was_cached,
        "retrieval_timestamp": retrieval_timestamp,
        "population_status": population_status,
        "population_count": population_count,
        "population_source": request.population_source,
    }

    db.add(
        AuditLog(
            actor_id="osm_importer",
            action="osm_batch_ingest",
            entity_type="osm_import_batch",
            entity_id=area.id if area else 0,
            new_value=json.dumps(batch_metadata),
            reason="Completed OpenStreetMap Overpass ingestion run",
        )
    )
    db.commit()

    summary = OSMImportSummary(
        total_osm_elements=total_elements,
        imported_count=imported_count,
        deduplicated_count=dedup_count,
        invalid_coordinates_count=invalid_coord_count,
        categories_imported=cat_counts,
        population_status=population_status,
        population_count=population_count,
        cached=was_cached,
        retrieval_timestamp=retrieval_timestamp,
        provenance=batch_metadata,
    )

    return OSMImportResponse(
        status="success",
        mode="real",
        is_demo_data=False,
        locality_name=request.locality_name or (area.name if area else "Custom Locality"),
        area_id=area.id if area else None,
        summary=summary,
        services_count=imported_count,
        provenance_notice=(
            "Data provided by OpenStreetMap contributors under Open Database License (ODbL). "
            "CivicPulse has verified coordinates and recorded data provenance. "
            "Population is preserved from documented public records without synthetic generation."
        ),
    )


def get_service_provenance(db: Session, service_id: int) -> Dict[str, Any]:
    """Retrieves stored data provenance, license attribution, and retrieval timestamp for a service."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise ValueError(f"Service with id {service_id} not found")

    is_demo = service.source_type == "simulated_demo"

    # Fetch audit log for specific provenance dictionary if imported from OSM
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "service")
        .filter(AuditLog.entity_id == service.id)
        .filter(AuditLog.action == "osm_import")
        .order_by(AuditLog.id.desc())
        .first()
    )

    provenance_info = {}
    if audit and audit.new_value:
        try:
            provenance_info = json.loads(audit.new_value)
        except Exception:
            provenance_info = {"raw": audit.new_value}

    retrieval_ts = (
        provenance_info.get("retrieval_timestamp")
        or (service.created_at.isoformat() if service.created_at else None)
    )

    license_str = (
        provenance_info.get("license", "ODbL 1.0 (Open Database License)")
        if service.source_type == "osm"
        else "Synthetic Demo License (Local Test Environment)"
    )

    return {
        "service_id": service.id,
        "service_name": service.name,
        "source_type": service.source_type,
        "is_demo_data": is_demo,
        "retrieval_timestamp": retrieval_ts,
        "confidence_score": float(service.confidence_score),
        "license": license_str,
        "provenance": provenance_info or {
            "source": service.source_type,
            "created_at": retrieval_ts,
            "is_demo_data": is_demo,
        },
    }
