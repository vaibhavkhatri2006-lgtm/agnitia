"""
GeoJSON conversion utilities for CivicPulse geospatial features.
Converts WKT, PostGIS representations, or Shapely geometries into standard RFC 7946 GeoJSON.
"""
import json
from typing import Any, Dict, Optional
from shapely import wkt
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry


def geometry_to_geojson_dict(geom_source: Any) -> Optional[Dict[str, Any]]:
    """
    Safely converts a geometry representation into a standard GeoJSON geometry dictionary.
    Handles:
    - WKT strings (e.g., 'MULTIPOLYGON (((...)))')
    - PostGIS EWKT strings (e.g., 'SRID=4326;POLYGON ((...))')
    - GeoJSON string representations
    - GeoJSON dictionary representations
    - Shapely geometry objects
    Returns None if source is null or unparseable.
    """
    if geom_source is None:
        return None

    try:
        if isinstance(geom_source, str):
            cleaned = geom_source.strip()
            if not cleaned:
                return None
            if ";" in cleaned:
                cleaned = cleaned.split(";", 1)[1].strip()
            if cleaned.startswith("{"):
                return json.loads(cleaned)
            geom_obj = wkt.loads(cleaned)
            return mapping(geom_obj)
        elif isinstance(geom_source, dict):
            return geom_source
        elif isinstance(geom_source, BaseGeometry):
            return mapping(geom_source)
        else:
            return None
    except Exception:
        return None


def point_to_geojson_dict(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Creates a valid GeoJSON Point geometry dictionary from latitude and longitude.
    GeoJSON coordinates format: [longitude, latitude].
    """
    if latitude is None or longitude is None:
        return None
    try:
        lat = float(latitude)
        lon = float(longitude)
        return {
            "type": "Point",
            "coordinates": [lon, lat],
        }
    except (ValueError, TypeError):
        return None
