"""
Candidate Location Engine (Stage 4A) for CivicPulse.
Identifies and validates deterministic candidate locations where new civic services
could be placed to address underserved areas and service gaps.
"""
import math
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session
from shapely import wkt
from shapely.geometry import Point, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from app.models import GeographicArea, ServiceCategory, Service, PopulationCell
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.analytics.distance import haversine_distance_km, extract_centroid_lat_lon


class CandidateLocation:
    """Represents a validated candidate location for potential civic service placement."""

    def __init__(
        self,
        candidate_id: str,
        service_type: str,
        latitude: float,
        longitude: float,
        area_id: int,
        area_name: str,
        source_reason: str,
        current_accessibility: float,
        population: int,
        current_gap: float,
        nearby_service_count: int,
        validity_status: str,
        strategy: str,
        rejection_reason: Optional[str] = None,
    ):
        self.candidate_id = candidate_id
        self.service_type = service_type
        self.latitude = latitude
        self.longitude = longitude
        self.area_id = area_id
        self.area_name = area_name
        self.source_reason = source_reason
        self.current_accessibility = current_accessibility
        self.population = population
        self.current_gap = current_gap
        self.nearby_service_count = nearby_service_count
        self.validity_status = validity_status
        self.strategy = strategy
        self.rejection_reason = rejection_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "service_type": self.service_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_id": self.area_id,
            "area_name": self.area_name,
            "source_reason": self.source_reason,
            "current_accessibility": self.current_accessibility,
            "population": self.population,
            "current_gap": self.current_gap,
            "nearby_service_count": self.nearby_service_count,
            "validity_status": self.validity_status,
            "strategy": self.strategy,
            "rejection_reason": self.rejection_reason,
        }


class CandidateLocationService:
    """
    Service layer responsible for generating, validating, and filtering
    candidate locations for new civic infrastructure.
    """

    SUPPORTED_SERVICES = [
        "healthcare",
        "education",
        "transport",
        "water",
        "market",
    ]

    def __init__(self, analytics_engine: Optional[AnalyticsEngine] = None):
        self.analytics = analytics_engine or default_analytics_engine

    # --- 1. Service Type Validation ---
    def validate_service_type(self, service_type: str) -> str:
        """
        Validates that the requested service type is supported.
        Raises ValueError if unsupported.
        """
        if not service_type or not isinstance(service_type, str):
            raise ValueError(
                f"Service type must be a non-empty string. Supported services: {', '.join(self.SUPPORTED_SERVICES)}"
            )

        norm_type = service_type.strip().lower()
        if norm_type not in self.SUPPORTED_SERVICES:
            raise ValueError(
                f"Unsupported service type '{service_type}'. Supported services: {', '.join(self.SUPPORTED_SERVICES)}"
            )
        return norm_type

    # --- 2. Geospatial Validation ---
    def validate_coordinates(self, latitude: float, longitude: float) -> Tuple[bool, Optional[str]]:
        """
        Verifies coordinate bounds and finiteness.
        Valid: -90 <= latitude <= 90, -180 <= longitude <= 180, not NaN or infinite.
        """
        if latitude is None or longitude is None:
            return False, "Coordinates cannot be None"

        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False, "Coordinates must be numeric floating-point values"

        if math.isnan(latitude) or math.isnan(longitude) or math.isinf(latitude) or math.isinf(longitude):
            return False, "Coordinates must be finite numbers"

        if not (-90.0 <= latitude <= 90.0):
            return False, f"Latitude {latitude} is outside valid range [-90, 90]"

        if not (-180.0 <= longitude <= 180.0):
            return False, f"Longitude {longitude} is outside valid range [-180, 180]"

        return True, None

    def validate_geometry(self, geom: Any) -> Tuple[bool, Optional[str]]:
        """Checks if a Shapely geometry is valid and non-empty."""
        if geom is None:
            return False, "Geometry is None"
        if not isinstance(geom, BaseGeometry):
            return False, "Geometry is not a valid Shapely BaseGeometry instance"
        if geom.is_empty:
            return False, "Geometry is empty"
        if not geom.is_valid:
            return False, "Geometry topology is invalid"
        return True, None

    def parse_geometry(self, geom_wkt: Optional[str], entity_label: str = "Geometry") -> Tuple[Optional[BaseGeometry], Optional[str]]:
        """Parses and validates a WKT geometry string."""
        if not geom_wkt:
            return None, f"{entity_label} has no defined geometry"
        try:
            geom = wkt.loads(geom_wkt)
            valid, reason = self.validate_geometry(geom)
            if not valid:
                return None, f"{entity_label} geometry invalid: {reason}"
            return geom, None
        except Exception as exc:
            return None, f"Failed to parse {entity_label} WKT geometry: {str(exc)}"

    def parse_area_geometry(self, area: GeographicArea) -> Tuple[Optional[BaseGeometry], Optional[str]]:
        """Parses and validates the WKT geometry of a GeographicArea."""
        area_name = getattr(area, "name", f"id={getattr(area, 'id', 'unknown')}")
        return self.parse_geometry(area.geometry, entity_label=f"Area '{area_name}'")

    def validate_point_in_area(
        self,
        latitude: float,
        longitude: float,
        area: GeographicArea,
        tolerance_degrees: float = 0.001,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies that a geographic point (lat, lon) is contained inside the area's polygon boundary.
        Uses a small tolerance buffer (0.001 deg ~ 110m) to accommodate boundary vertices.
        """
        coord_valid, coord_reason = self.validate_coordinates(latitude, longitude)
        if not coord_valid:
            return False, coord_reason

        geom, geom_reason = self.parse_area_geometry(area)
        if not geom:
            return False, geom_reason

        # Coordinate order in Shapely is (x, y) = (longitude, latitude)
        pt = Point(longitude, latitude)
        if not pt.is_valid:
            return False, "Point geometry is invalid"

        # Check containment or boundary intersection
        if geom.contains(pt) or geom.touches(pt):
            return True, None

        if geom.buffer(tolerance_degrees).contains(pt):
            return True, None

        return False, f"Point ({latitude}, {longitude}) lies outside boundary of area '{area.name}'"

    # --- 3. Underserved Area Filtering ---
    def find_underserved_areas(
        self,
        db: Session,
        service_type: str,
        min_gap_threshold: float = 20.0,
        max_accessibility: float = 80.0,
    ) -> List[Tuple[GeographicArea, Dict[str, Any]]]:
        """
        Scans analysis areas and identifies those with meaningful service gaps.
        Excludes areas where the selected service is already sufficiently available
        (e.g., accessibility > max_accessibility or Well Served).
        """
        norm_type = self.validate_service_type(service_type)
        category = db.query(ServiceCategory).filter_by(code=norm_type).first()
        if not category:
            return []

        # Analyze analysis units (neighbourhoods and districts)
        areas = (
            db.query(GeographicArea)
            .filter(GeographicArea.area_type.in_(["neighbourhood", "district"]))
            .order_by(GeographicArea.id)
            .all()
        )

        underserved: List[Tuple[GeographicArea, Dict[str, Any]]] = []
        for area in areas:
            metrics = self.analytics.analyze_area_category(db, area, category)
            acc = metrics["accessibility_score"]
            gap = metrics["gap_score"]

            # Exclude locations where service is already sufficiently available
            if acc >= max_accessibility or metrics["service_desert_classification"] == "Well Served":
                continue

            # Check if area has a meaningful gap
            if gap >= min_gap_threshold:
                underserved.append((area, metrics))

        # Sort deterministically by gap score descending (most underserved first), then by area_id
        underserved.sort(key=lambda item: (-item[1]["gap_score"], item[0].id))
        return underserved

    # --- 4. Candidate Generation Core ---
    def generate_candidates_for_service(
        self,
        db: Session,
        service_type: str,
        min_gap_threshold: float = 20.0,
        max_accessibility: float = 80.0,
        include_rejected: bool = False,
    ) -> List[CandidateLocation]:
        """
        Generates a deterministic set of candidate locations for the specified service type.
        Applies multi-strategy candidate generation across qualifying underserved areas.
        Validates all points and discards/flags duplicates and invalid coordinates.
        """
        norm_type = self.validate_service_type(service_type)
        category = db.query(ServiceCategory).filter_by(code=norm_type).first()
        if not category:
            return []

        underserved_areas = self.find_underserved_areas(
            db=db,
            service_type=norm_type,
            min_gap_threshold=min_gap_threshold,
            max_accessibility=max_accessibility,
        )

        # Existing services of this category (used for proximity and coverage calculations)
        existing_services = db.query(Service).filter_by(category_id=category.id).all()

        raw_candidates: List[CandidateLocation] = []
        seen_coordinates: Set[Tuple[float, float]] = set()

        for area, metrics in underserved_areas:
            area_geom, geom_err = self.parse_area_geometry(area)
            if not area_geom:
                # Area has invalid/missing geometry: record rejected candidate safely and continue
                raw_candidates.append(
                    CandidateLocation(
                        candidate_id=f"cand-{norm_type}-{area.id}-invalidgeom",
                        service_type=norm_type,
                        latitude=0.0,
                        longitude=0.0,
                        area_id=area.id,
                        area_name=area.name,
                        source_reason=f"Area {area.name} requires intervention but has invalid geometry",
                        current_accessibility=metrics["accessibility_score"],
                        population=area.population,
                        current_gap=metrics["gap_score"],
                        nearby_service_count=0,
                        validity_status="rejected",
                        strategy="area_centroid",
                        rejection_reason=geom_err or "Invalid area geometry",
                    )
                )
                continue

            # Nearby services count for this area
            nearby_count = 0
            for svc in existing_services:
                dist = haversine_distance_km(
                    area_geom.centroid.y, area_geom.centroid.x, svc.latitude, svc.longitude
                )
                if dist <= self.analytics.config.max_catchment_distance_km:
                    nearby_count += 1

            # --- Strategy 1: Area Centroid / Interior Representative Point ---
            centroid = area_geom.centroid
            if area_geom.contains(centroid):
                pt1 = centroid
            else:
                pt1 = area_geom.representative_point()

            cand1_lat = round(pt1.y, 6)
            cand1_lon = round(pt1.x, 6)
            coord_key1 = (cand1_lat, cand1_lon)

            valid1, reason1 = self.validate_point_in_area(cand1_lat, cand1_lon, area)
            status1 = "valid" if valid1 else "rejected"

            if coord_key1 not in seen_coordinates:
                seen_coordinates.add(coord_key1)
                raw_candidates.append(
                    CandidateLocation(
                        candidate_id=f"cand-{norm_type}-{area.id}-centroid",
                        service_type=norm_type,
                        latitude=cand1_lat,
                        longitude=cand1_lon,
                        area_id=area.id,
                        area_name=area.name,
                        source_reason=f"Geometric interior center of underserved area {area.name} (Gap: {metrics['gap_score']}%)",
                        current_accessibility=metrics["accessibility_score"],
                        population=area.population,
                        current_gap=metrics["gap_score"],
                        nearby_service_count=nearby_count,
                        validity_status=status1,
                        strategy="centroid",
                        rejection_reason=reason1,
                    )
                )

            # --- Strategy 2: Population Node / Demand Center ---
            pop_cells = db.query(PopulationCell).filter_by(area_id=area.id).all()
            if pop_cells:
                top_cell = max(pop_cells, key=lambda c: c.population)
                cell_geom, _ = self.parse_geometry(top_cell.geometry, entity_label=f"PopulationCell id={top_cell.id}")
                if cell_geom:
                    c_pt = cell_geom.centroid if area_geom.contains(cell_geom.centroid) else cell_geom.representative_point()
                else:
                    c_pt = area_geom.representative_point()
                pop_reason = f"High-density population cluster ({top_cell.population:,} residents) in {area.name}"
            else:
                # If no sub-cells, derive deterministic secondary interior node
                c_pt = area_geom.representative_point()
                pop_reason = f"Primary community demand node in {area.name} (Population: {area.population:,})"

            cand2_lat = round(c_pt.y, 6)
            cand2_lon = round(c_pt.x, 6)
            coord_key2 = (cand2_lat, cand2_lon)

            # Deduplication: check if coordinate already captured by centroid
            if not self._is_coordinate_duplicate(coord_key2, seen_coordinates):
                valid2, reason2 = self.validate_point_in_area(cand2_lat, cand2_lon, area)
                status2 = "valid" if valid2 else "rejected"
                seen_coordinates.add(coord_key2)
                raw_candidates.append(
                    CandidateLocation(
                        candidate_id=f"cand-{norm_type}-{area.id}-popnode",
                        service_type=norm_type,
                        latitude=cand2_lat,
                        longitude=cand2_lon,
                        area_id=area.id,
                        area_name=area.name,
                        source_reason=pop_reason,
                        current_accessibility=metrics["accessibility_score"],
                        population=area.population,
                        current_gap=metrics["gap_score"],
                        nearby_service_count=nearby_count,
                        validity_status=status2,
                        strategy="population_node",
                        rejection_reason=reason2,
                    )
                )

            # --- Strategy 3: Coverage Gap Maximizer (Furthest Valid Point from Existing Facilities) ---
            boundary_cand = self._find_gap_maximizing_point(area_geom, existing_services)
            if boundary_cand:
                cand3_lat = round(boundary_cand.y, 6)
                cand3_lon = round(boundary_cand.x, 6)
                coord_key3 = (cand3_lat, cand3_lon)

                if not self._is_coordinate_duplicate(coord_key3, seen_coordinates):
                    valid3, reason3 = self.validate_point_in_area(cand3_lat, cand3_lon, area)
                    status3 = "valid" if valid3 else "rejected"
                    seen_coordinates.add(coord_key3)
                    raw_candidates.append(
                        CandidateLocation(
                            candidate_id=f"cand-{norm_type}-{area.id}-gapzone",
                            service_type=norm_type,
                            latitude=cand3_lat,
                            longitude=cand3_lon,
                            area_id=area.id,
                            area_name=area.name,
                            source_reason=f"Coverage gap zone in {area.name} maximizing distance from existing facilities",
                            current_accessibility=metrics["accessibility_score"],
                            population=area.population,
                            current_gap=metrics["gap_score"],
                            nearby_service_count=nearby_count,
                            validity_status=status3,
                            strategy="gap_perimeter",
                            rejection_reason=reason3,
                        )
                    )

        # Filter rejected if not requested
        if not include_rejected:
            candidates = [c for c in raw_candidates if c.validity_status == "valid"]
        else:
            candidates = raw_candidates

        # Ensure 100% deterministic ordering
        candidates.sort(key=lambda c: (c.area_id, c.strategy, c.candidate_id))
        return candidates

    def _is_coordinate_duplicate(
        self,
        coord: Tuple[float, float],
        seen_coords: Set[Tuple[float, float]],
        tolerance: float = 0.0001,
    ) -> bool:
        """Checks if a coordinate is practically identical to an already seen coordinate."""
        lat, lon = coord
        for s_lat, s_lon in seen_coords:
            if abs(lat - s_lat) < tolerance and abs(lon - s_lon) < tolerance:
                return True
        return False

    def _find_gap_maximizing_point(
        self,
        area_geom: BaseGeometry,
        existing_services: List[Service],
    ) -> Optional[Point]:
        """
        Deterministically evaluates sample interior points of an area polygon
        and returns the point that maximizes distance to nearest existing facility.
        """
        # Collect candidate sample points deterministically
        sample_points: List[Point] = []
        if isinstance(area_geom, (Polygon, MultiPolygon)):
            # Sample exterior vertices nudged slightly inward
            rep = area_geom.representative_point()
            sample_points.append(rep)

            # Sample bbox boundary midpoints
            minx, miny, maxx, maxy = area_geom.bounds
            mid_pt = Point((minx + maxx) / 2.0, (miny + maxy) / 2.0)
            if area_geom.contains(mid_pt):
                sample_points.append(mid_pt)

            corner_pts = [
                Point(minx + (maxx - minx) * 0.25, miny + (maxy - miny) * 0.25),
                Point(maxx - (maxx - minx) * 0.25, maxy - (maxy - miny) * 0.25),
                Point(minx + (maxx - minx) * 0.25, maxy - (maxy - miny) * 0.25),
                Point(maxx - (maxx - minx) * 0.25, miny + (maxy - miny) * 0.25),
            ]
            for cp in corner_pts:
                if area_geom.contains(cp):
                    sample_points.append(cp)

        if not sample_points:
            return area_geom.representative_point()

        if not existing_services:
            # If no existing services, return first valid interior point
            return sample_points[0]

        # Find point maximizing minimum distance to existing facilities
        best_point: Optional[Point] = None
        max_min_dist = -1.0

        for pt in sample_points:
            min_dist_to_svc = min(
                haversine_distance_km(pt.y, pt.x, svc.latitude, svc.longitude)
                for svc in existing_services
            )
            if min_dist_to_svc > max_min_dist:
                max_min_dist = min_dist_to_svc
                best_point = pt

        return best_point or sample_points[0]


# Singleton instance
default_candidate_service = CandidateLocationService()
