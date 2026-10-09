"""
Pydantic Schemas for Real Data Mode and OpenStreetMap Integration.
Defines contracts for operational mode switching, Overpass OSM data import,
provenance metadata, and caching statistics.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CivicPulseModeResponse(BaseModel):
    """Current operational mode of CivicPulse."""
    mode: str = Field(..., description="Active mode: 'demo' or 'real'")
    description: str = Field(..., description="Explanation of current data mode")
    demo_available: bool = Field(True, description="Whether deterministic demo dataset is available")
    real_available: bool = Field(True, description="Whether real OpenStreetMap ingestion is available")
    active_sources: List[str] = Field(..., description="Active data source tags in current mode")
    osrm_enabled: bool = Field(False, description="Whether OSRM network routing is active")
    osrm_configured: bool = Field(False, description="Whether OSRM base URL is configured")


class CivicPulseModeUpdateRequest(BaseModel):
    """Payload to toggle CivicPulse operational mode."""
    mode: str = Field(..., description="Target mode: 'demo' or 'real'", json_schema_extra={"example": "real"})


class OSMImportRequest(BaseModel):
    """Specification of target locality for OpenStreetMap data retrieval."""
    locality_name: Optional[str] = Field(None, description="Name of target locality (e.g. 'Koramangala, Bengaluru')")
    area_id: Optional[int] = Field(None, description="Optional ID of existing geographic area to associate with")
    bbox: Optional[List[float]] = Field(
        None,
        description="Bounding box coordinates [south, west, north, east]",
        json_schema_extra={"example": [12.925, 77.610, 12.945, 77.635]},
    )
    center_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Center latitude")
    center_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Center longitude")
    radius_meters: Optional[float] = Field(2000.0, ge=100.0, le=50000.0, description="Search radius in meters")
    categories: Optional[List[str]] = Field(
        None,
        description="Optional list of service categories to fetch: healthcare, education, transport, water, market",
    )
    documented_population: Optional[int] = Field(
        None,
        ge=0,
        description="Documented population from official census or public dataset if available. If None, population is marked unavailable.",
    )
    population_source: Optional[str] = Field(
        None,
        description="Documented source name/citation for population data (e.g. 'Census 2021 Table B')",
    )


class OSMImportSummary(BaseModel):
    """Summary metrics of the OSM data import operation."""
    total_osm_elements: int = Field(..., description="Total raw elements returned by Overpass query")
    imported_count: int = Field(..., description="Number of new valid services stored")
    deduplicated_count: int = Field(..., description="Number of duplicate services skipped")
    invalid_coordinates_count: int = Field(..., description="Number of elements with invalid coordinates rejected")
    categories_imported: Dict[str, int] = Field(..., description="Count of imported services per category")
    population_status: str = Field(..., description="'documented' or 'unavailable'")
    population_count: Optional[int] = Field(None, description="Resident population if documented, otherwise None")
    cached: bool = Field(..., description="Whether query was served from local Overpass cache")
    retrieval_timestamp: str = Field(..., description="ISO 8601 timestamp of data retrieval")
    provenance: Dict[str, Any] = Field(..., description="Data provenance metadata")


class OSMImportResponse(BaseModel):
    """Result of OpenStreetMap data retrieval and ingestion."""
    status: str = Field(..., description="'success' or 'partial'")
    mode: str = Field("real", description="Operational mode: 'real'")
    is_demo_data: bool = Field(False, description="Guaranteed False for real OSM imported data")
    locality_name: str = Field(..., description="Locality name")
    area_id: Optional[int] = Field(None, description="Associated geographic area ID")
    summary: OSMImportSummary = Field(..., description="Import execution summary")
    services_count: int = Field(..., description="Total imported services count")
    provenance_notice: str = Field(..., description="Legal license and data provenance statement")


class OSMCacheStatsResponse(BaseModel):
    """Telemetry for Overpass query cache and rate limiting."""
    cache_entries: int = Field(..., description="Number of cached query results")
    cache_hits: int = Field(..., description="Number of queries served from cache")
    cache_misses: int = Field(..., description="Number of live API queries executed")
    rate_limit_cooldown_seconds: float = Field(..., description="Configured cooldown between live queries")
    user_agent: str = Field(..., description="User-Agent string sent to Overpass API")


class ServiceProvenanceResponse(BaseModel):
    """Data provenance details for a specific civic service facility."""
    service_id: int
    service_name: str
    source_type: str
    is_demo_data: bool
    retrieval_timestamp: Optional[str] = None
    confidence_score: float
    license: str
    provenance: Dict[str, Any]
