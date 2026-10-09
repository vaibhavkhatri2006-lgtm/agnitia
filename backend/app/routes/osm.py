"""
OpenStreetMap & Real Data API Routes for CivicPulse.
Provides endpoints for Overpass QL query generation, locality data import,
cache telemetry, and facility data provenance verification.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.real_data import (
    OSMImportRequest,
    OSMImportResponse,
    OSMCacheStatsResponse,
    ServiceProvenanceResponse,
    OSMQueryResponse,
)
from app.services.osm_service import (
    build_overpass_query,
    import_osm_locality_data,
    get_cache_stats,
    clear_osm_cache,
    get_service_provenance,
    fetch_normalized_osm_services,
)

router = APIRouter(prefix="/osm", tags=["OpenStreetMap Ingestion"])


@router.post(
    "/import",
    response_model=OSMImportResponse,
    summary="Import civic infrastructure from OpenStreetMap for a target locality",
)
def import_locality_osm(
    request: OSMImportRequest,
    db: Session = Depends(get_db),
):
    """
    Retrieves real-world civic services (clinics, hospitals, schools, transport stops, water points, markets)
    from OpenStreetMap via Overpass API for the designated locality.
    - Validates geographic coordinates.
    - Deduplicates against existing facility records.
    - Stores complete data provenance and retrieval timestamps.
    - Preserves documented population without synthetic generation.
    """
    try:
        response = import_osm_locality_data(db, request)
        return response
    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStreetMap Overpass provider error: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process OpenStreetMap data import: {err}",
        )


@router.get(
    "/services",
    response_model=OSMQueryResponse,
    summary="Query and normalize civic infrastructure from OpenStreetMap via Overpass",
)
def get_normalized_services(
    locality_name: Optional[str] = Query(None, description="Name of target locality (e.g. 'Koramangala')"),
    area_id: Optional[int] = Query(None, description="Database ID of geographic area"),
    categories: Optional[List[str]] = Query(None, description="Service categories to retrieve (healthcare, education, transport, water, market)"),
    min_lat: Optional[float] = Query(None, description="South bounding latitude"),
    min_lon: Optional[float] = Query(None, description="West bounding longitude"),
    max_lat: Optional[float] = Query(None, description="North bounding latitude"),
    max_lon: Optional[float] = Query(None, description="East bounding longitude"),
    center_lat: Optional[float] = Query(None, description="Center latitude"),
    center_lon: Optional[float] = Query(None, description="Center longitude"),
    radius_meters: float = Query(2000.0, description="Search radius in meters"),
    fallback_to_demo: bool = Query(True, description="Fallback to deterministic local data if Overpass is unavailable"),
    force_live: bool = Query(False, description="Force live Overpass query even in DEMO_MODE"),
    db: Session = Depends(get_db),
):
    """
    Overpass Data Provider Endpoint:
    Retrieves hospitals, clinics, doctors, schools, colleges, universities, bus stops,
    and civic amenities for the selected locality.

    Returns normalized records conforming to strict schema:
    OSM ID, name, service category, latitude, longitude, tags, and source.
    Correctly handles both point features (nodes) and area features (ways/relations)
    using representative coordinates for mapped areas.
    """
    bbox = None
    if all(v is not None for v in (min_lat, min_lon, max_lat, max_lon)):
        bbox = [min_lat, min_lon, max_lat, max_lon]

    try:
        response = fetch_normalized_osm_services(
            db=db,
            locality_name=locality_name,
            area_id=area_id,
            bbox=bbox,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_meters=radius_meters,
            categories=categories,
            fallback_to_demo=fallback_to_demo,
            force_live=force_live,
        )
        return response
    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStreetMap Overpass API error: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query OpenStreetMap services: {err}",
        )


@router.post(
    "/services",
    response_model=OSMQueryResponse,
    summary="Query and normalize civic infrastructure from OpenStreetMap with JSON payload",
)
def post_normalized_services(
    request: OSMImportRequest,
    fallback_to_demo: bool = Query(True, description="Fallback to deterministic local data if Overpass is unavailable"),
    force_live: bool = Query(False, description="Force live Overpass query even in DEMO_MODE"),
    db: Session = Depends(get_db),
):
    """
    POST variant of Overpass Data Provider accepting JSON body.
    """
    try:
        response = fetch_normalized_osm_services(
            db=db,
            locality_name=request.locality_name,
            area_id=request.area_id,
            bbox=request.bbox,
            center_lat=request.center_latitude,
            center_lon=request.center_longitude,
            radius_meters=request.radius_meters or 2000.0,
            categories=request.categories,
            fallback_to_demo=fallback_to_demo,
            force_live=force_live,
        )
        return response
    except RuntimeError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStreetMap Overpass API error: {err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query OpenStreetMap services: {err}",
        )


@router.get(
    "/query",
    summary="Preview generated Overpass QL query for a locality",
)
def preview_overpass_query(
    categories: Optional[List[str]] = Query(None, description="Categories to include"),
    min_lat: Optional[float] = Query(None, description="South latitude"),
    min_lon: Optional[float] = Query(None, description="West longitude"),
    max_lat: Optional[float] = Query(None, description="North latitude"),
    max_lon: Optional[float] = Query(None, description="East longitude"),
    center_lat: Optional[float] = Query(None, description="Center latitude"),
    center_lon: Optional[float] = Query(None, description="Center longitude"),
    radius_meters: float = Query(2000.0, description="Search radius in meters"),
):
    """
    Returns the exact Overpass QL query string constructed for given parameters.
    Allows inspection of the query without executing an external network call.
    """
    bbox = None
    if all(v is not None for v in (min_lat, min_lon, max_lat, max_lon)):
        bbox = [min_lat, min_lon, max_lat, max_lon]

    query_str = build_overpass_query(
        categories=categories,
        bbox=bbox,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_meters=radius_meters,
    )
    return {
        "overpass_ql": query_str,
        "endpoint": "https://overpass-api.de/api/interpreter",
        "description": "Deterministic Overpass QL targeting healthcare, education, transport, water, and market facilities.",
    }


@router.get(
    "/cache/stats",
    response_model=OSMCacheStatsResponse,
    summary="Get Overpass query cache and rate-limiting telemetry",
)
def get_osm_cache_stats():
    """
    Returns statistics on Overpass API query caching and cooldown adherence.
    """
    stats = get_cache_stats()
    return OSMCacheStatsResponse(**stats)


@router.post(
    "/cache/clear",
    summary="Clear the Overpass query cache",
)
def clear_cache():
    """
    Flushes all cached Overpass query responses.
    """
    cleared_count = clear_osm_cache()
    return {
        "status": "success",
        "cleared_entries": cleared_count,
        "message": f"Successfully cleared {cleared_count} Overpass cached query records.",
    }


@router.get(
    "/provenance/{service_id}",
    response_model=ServiceProvenanceResponse,
    summary="Inspect data provenance and license attribution for a service",
)
def inspect_service_provenance(
    service_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns full data provenance, retrieval timestamp, OpenStreetMap tags/id (if imported),
    and license terms for a civic facility.
    """
    try:
        prov = get_service_provenance(db, service_id)
        return ServiceProvenanceResponse(**prov)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
