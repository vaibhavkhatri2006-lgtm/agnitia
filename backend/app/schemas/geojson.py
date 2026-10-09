"""
GeoJSON schemas conforming to RFC 7946.
Supports Feature and FeatureCollection models for localities and facility point layers.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    """Represents a GeoJSON geometry object (Point, Polygon, MultiPolygon, etc.)."""
    type: str = Field(..., description="Geometry type (e.g. Point, Polygon, MultiPolygon)")
    coordinates: Any = Field(..., description="Coordinate values conforming to GeoJSON RFC 7946")


class GeoJSONFeature(BaseModel):
    """Represents a standard GeoJSON Feature object."""
    type: str = Field("Feature", description="Must be 'Feature'")
    id: Optional[Any] = Field(None, description="Optional feature identifier")
    geometry: Optional[GeoJSONGeometry] = Field(None, description="GeoJSON geometry or null if unlocated")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature attributes and analytical properties")


class GeoJSONFeatureCollection(BaseModel):
    """Represents a GeoJSON FeatureCollection."""
    type: str = Field("FeatureCollection", description="Must be 'FeatureCollection'")
    features: List[GeoJSONFeature] = Field(default_factory=list, description="Array of GeoJSON Feature objects")
