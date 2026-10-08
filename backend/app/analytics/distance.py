import math
import json
from typing import Tuple, Dict, Any, Optional
from shapely import wkt
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from app.analytics.config import default_analytics_config, AnalyticsConfig


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two coordinates in kilometers using the Haversine formula.
    Accurate for regional and urban geospatial calculations.
    """
    R = 6371.0  # Earth's mean radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns Haversine distance in meters."""
    return haversine_distance_km(lat1, lon1, lat2, lon2) * 1000.0


def extract_centroid_lat_lon(geometry_wkt_or_geom) -> Tuple[float, float]:
    """
    Extracts the (latitude, longitude) center of a geometry.
    Supports WKT strings, GeoJSON strings/dicts, or Shapely geometries.
    Note: Coordinate order is (x, y) = (longitude, latitude).
    Returns: (latitude, longitude).
    """
    if isinstance(geometry_wkt_or_geom, str):
        cleaned = geometry_wkt_or_geom.strip()
        if cleaned.startswith("{"):
            geom = shape(json.loads(cleaned))
        else:
            geom = wkt.loads(cleaned)
    elif isinstance(geometry_wkt_or_geom, dict):
        geom = shape(geometry_wkt_or_geom)
    elif isinstance(geometry_wkt_or_geom, BaseGeometry):
        geom = geometry_wkt_or_geom
    else:
        raise ValueError(f"Unsupported geometry type: {type(geometry_wkt_or_geom)}")

    centroid = geom.centroid
    return centroid.y, centroid.x  # latitude (y), longitude (x)


class RoutingProvider:
    """Abstract routing interface so real network providers (OSRM, Valhalla) can be integrated later."""

    def estimate_travel(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str = "transit",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class DeterministicRoutingProvider(RoutingProvider):
    """
    Deterministic travel-time calculation layer.
    Computes geometric distance and applies a configurable urban detour factor (1.30)
    and assumed travel speeds to produce reproducible travel time estimates.
    """

    def __init__(self, config: Optional[AnalyticsConfig] = None):
        self.config = config or default_analytics_config

    def estimate_travel(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str = "transit",
    ) -> Dict[str, Any]:
        direct_distance_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)

        # Urban street grid detour factor (typical 1.30x Euclidean distance in cities)
        detour_factor = 1.30
        estimated_network_distance_km = direct_distance_km * detour_factor

        if mode == "walking":
            speed_kmh = self.config.walking_speed_kmh
        elif mode == "driving":
            speed_kmh = self.config.driving_speed_kmh
        else:  # transit (default)
            speed_kmh = self.config.transit_speed_kmh

        # travel_time_minutes = (distance / speed) * 60
        travel_time_minutes = (estimated_network_distance_km / speed_kmh) * 60.0

        return {
            "direct_distance_km": round(direct_distance_km, 3),
            "estimated_network_distance_km": round(estimated_network_distance_km, 3),
            "estimated_travel_time_minutes": round(travel_time_minutes, 1),
            "mode": mode,
            "assumed_speed_kmh": speed_kmh,
            "detour_factor": detour_factor,
            "is_estimate": True,
            "provider": "deterministic_approximation",
        }


class OSRMRoutingProvider(RoutingProvider):
    """
    Routing provider that queries an OSRM instance when configured and enabled.
    Gracefully falls back to DeterministicRoutingProvider on any failure, timeout, or error.
    Clearly labels estimated travel times and provider provenance.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 3.0,
        fallback_provider: Optional[RoutingProvider] = None,
    ):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.fallback_provider = fallback_provider or DeterministicRoutingProvider()

    def estimate_travel(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        mode: str = "transit",
    ) -> Dict[str, Any]:
        # If not configured, immediately use deterministic fallback
        if not self.base_url:
            res = self.fallback_provider.estimate_travel(origin_lat, origin_lon, dest_lat, dest_lon, mode)
            res["provider"] = "deterministic_approximation"
            return res

        # Map mode to OSRM profile (car, foot)
        profile = "foot" if mode == "walking" else "car"
        direct_distance_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)

        try:
            import httpx

            url = f"{self.base_url.rstrip('/')}/route/v1/{profile}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=false"
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        duration_sec = route.get("duration", 0.0)
                        distance_m = route.get("distance", 0.0)
                        return {
                            "direct_distance_km": round(direct_distance_km, 3),
                            "estimated_network_distance_km": round(distance_m / 1000.0, 3),
                            "estimated_travel_time_minutes": round(max(1.0, duration_sec / 60.0), 1),
                            "mode": mode,
                            "is_estimate": True,
                            "provider": "osrm",
                            "osrm_profile": profile,
                        }
        except Exception:
            # Graceful fallback on network timeout, connection error, etc.
            pass

        # Fallback to deterministic approximation
        res = self.fallback_provider.estimate_travel(origin_lat, origin_lon, dest_lat, dest_lon, mode)
        res["provider"] = "fallback_deterministic"
        res["provider_warning"] = "OSRM routing unavailable or failed; deterministic fallback used"
        return res


default_deterministic_routing_provider = DeterministicRoutingProvider()


def get_routing_provider() -> RoutingProvider:
    """Returns active routing provider based on system settings."""
    try:
        from app.config import settings

        if settings.USE_OSRM and settings.OSRM_BASE_URL:
            return OSRMRoutingProvider(
                base_url=settings.OSRM_BASE_URL,
                timeout_seconds=settings.OSRM_TIMEOUT_SECONDS,
                fallback_provider=default_deterministic_routing_provider,
            )
    except Exception:
        pass
    return default_deterministic_routing_provider


# Default active routing provider (dispatches to OSRM if configured or deterministic fallback)
default_routing_provider = default_deterministic_routing_provider
