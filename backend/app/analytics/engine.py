import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.analytics.config import default_analytics_config, AnalyticsConfig
from app.analytics.distance import (
    haversine_distance_km,
    extract_centroid_lat_lon,
    default_routing_provider,
    RoutingProvider,
)
from app.models import (
    GeographicArea,
    ServiceCategory,
    Service,
    ServiceCapacity,
    PopulationCell,
    CommunityReport,
    DataSource,
)


class AnalyticsEngine:
    """
    Core Deterministic Geospatial & Analytics Engine for CivicPulse.
    Calculates Accessibility Scores, Gap Scores, Service Deserts, Service Pressure,
    Equity Scores, Confidence Scores, and Reality Gap metrics.
    """

    def __init__(
        self,
        config: Optional[AnalyticsConfig] = None,
        routing_provider: Optional[RoutingProvider] = None,
    ):
        self.config = config or default_analytics_config
        self.routing = routing_provider or default_routing_provider

    # --- 1. Travel-Time Score ---
    def calculate_travel_time_score(self, travel_time_minutes: float) -> float:
        """
        Converts travel time into a normalized 0–100 score using the baseline threshold model:
        0–10 min   = 100
        10–20 min  = 80
        20–30 min  = 60
        30–45 min  = 35
        > 45 min   = 10
        (infinite/unreachable = 0)
        """
        if travel_time_minutes == float("inf") or travel_time_minutes is None:
            return 0.0

        for max_mins, score in self.config.travel_time_thresholds:
            if travel_time_minutes <= max_mins:
                return float(score)

        return 10.0

    # --- 2. Service Availability Score ---
    def calculate_availability_score(self, service: Optional[Service]) -> float:
        """
        Maps service operational state to a deterministic 0-100 score:
        operational: 100, limited: 60, degraded: 50, temporarily_unavailable: 20, closed: 0
        """
        if service is None:
            return 0.0

        status_key = (service.status or "closed").lower().strip()
        return float(self.config.availability_scores.get(status_key, 0.0))

    # --- 3. Capacity Score & Service Pressure ---
    def calculate_capacity_and_pressure(
        self,
        service: Optional[Service],
        demand_population: int,
    ) -> Dict[str, Any]:
        """
        Calculates normalized capacity score (0-100) and service pressure category/ratio.
        Gracefully handles missing, zero, constrained, and sufficient capacity without crashing.
        """
        if service is None:
            return {
                "capacity_score": 0.0,
                "pressure_ratio": 999.0 if demand_population > 0 else 0.0,
                "pressure_category": "Critical" if demand_population > 0 else "Low",
                "pressure_score": 0.0,
                "capacity": 0,
                "current_load": 0,
                "data_quality": "no_service_available",
            }

        cap_record: Optional[ServiceCapacity] = service.capacity_record
        if cap_record is None or cap_record.capacity is None:
            # Unreported capacity: return neutral score with data quality note
            return {
                "capacity_score": 50.0,
                "pressure_ratio": 1.0,
                "pressure_category": "Moderate",
                "pressure_score": 50.0,
                "capacity": None,
                "current_load": None,
                "data_quality": "unreported",
            }

        capacity = max(0, cap_record.capacity)
        load = max(0, cap_record.current_load if cap_record.current_load is not None else 0)

        if capacity == 0:
            return {
                "capacity_score": 0.0,
                "pressure_ratio": 999.0 if demand_population > 0 else 0.0,
                "pressure_category": "Critical" if demand_population > 0 else "Low",
                "pressure_score": 0.0,
                "capacity": 0,
                "current_load": load,
                "data_quality": "zero_capacity",
            }

        # Capacity score calculation (0 to 100)
        load_ratio = load / capacity
        if load_ratio > 1.0:
            # Overloaded
            raw_cap_score = max(10.0, 100.0 - (load_ratio - 1.0) * 100.0)
        else:
            # Normal or under capacity
            raw_cap_score = min(100.0, 60.0 + (1.0 - load_ratio) * 40.0)

        # Service pressure = Demand / Available Capacity
        pressure_ratio = round(demand_population / capacity, 2)
        if pressure_ratio < 0.8:
            pressure_cat = "Low"
            pressure_score = 90.0
            capacity_score = raw_cap_score
        elif pressure_ratio < 1.2:
            pressure_cat = "Moderate"
            pressure_score = 70.0
            capacity_score = min(raw_cap_score, 80.0)
        elif pressure_ratio < 2.0:
            pressure_cat = "High"
            pressure_score = 40.0
            capacity_score = min(raw_cap_score, 50.0)
        else:
            pressure_cat = "Critical"
            pressure_score = 15.0
            capacity_score = min(raw_cap_score, 20.0)

        return {
            "capacity_score": round(capacity_score, 1),
            "pressure_ratio": pressure_ratio,
            "pressure_category": pressure_cat,
            "pressure_score": pressure_score,
            "capacity": capacity,
            "current_load": load,
            "data_quality": "verified_record",
        }

    # --- 4. Transport Connectivity Score ---
    def calculate_transport_connectivity(
        self,
        db: Session,
        area_lat: float,
        area_lon: float,
    ) -> float:
        """
        Evaluates connectivity to public transit from the area center.
        """
        transport_cat = db.query(ServiceCategory).filter_by(code="transport").first()
        if not transport_cat:
            return 50.0

        transit_services = db.query(Service).filter_by(category_id=transport_cat.id).all()
        if not transit_services:
            return 10.0

        best_score = 0.0
        for svc in transit_services:
            dist_km = haversine_distance_km(area_lat, area_lon, svc.latitude, svc.longitude)
            avail = self.calculate_availability_score(svc)
            # Distance penalty: optimal <= 1.0 km, degrades up to 5.0 km
            dist_score = max(0.0, 100.0 - (dist_km / 5.0) * 80.0)
            score = (dist_score * 0.60) + (avail * 0.40)
            if score > best_score:
                best_score = score

        return round(max(0.0, min(100.0, best_score)), 1)

    # --- 5. Equity Score ---
    def calculate_equity_score(
        self,
        area: GeographicArea,
        preliminary_access_score: float,
    ) -> float:
        """
        Evaluates equity score based on demographic vulnerability and access.
        Areas with high demographic vulnerability require high service accessibility
        to achieve a good equity score.
        """
        # Extract demographic vulnerability from population cells
        vulnerability_indices = []
        for cell in area.population_cells:
            if cell.demographics:
                try:
                    data = json.loads(cell.demographics)
                    if "vulnerability_index" in data:
                        vulnerability_indices.append(float(data["vulnerability_index"]))
                except Exception:
                    pass

        avg_vulnerability = (
            sum(vulnerability_indices) / len(vulnerability_indices)
            if vulnerability_indices
            else 0.35  # default baseline
        )

        # If area has high vulnerability (e.g. 0.70+) but poor access (< 50), equity score drops severely
        if preliminary_access_score >= 70.0:
            equity = 90.0 + (10.0 * (1.0 - avg_vulnerability))
        elif preliminary_access_score >= 40.0:
            equity = 60.0 - (avg_vulnerability * 25.0)
        else:
            # Underserved vulnerable community: severe equity gap
            equity = max(5.0, 35.0 - (avg_vulnerability * 30.0))

        return round(max(0.0, min(100.0, equity)), 1)

    # --- 6. Confidence Score & Reality Gap ---
    def calculate_confidence_and_reality_gap(
        self,
        db: Session,
        area: GeographicArea,
        category: ServiceCategory,
        nearest_service: Optional[Service],
    ) -> Dict[str, Any]:
        """
        Calculates data confidence score (0.0 to 1.0) and reality gap divergence
        between nominal operational status and active community reports.
        """
        # Baseline confidence from source types and service confidence
        if nearest_service:
            source = db.query(DataSource).filter_by(code=nearest_service.source_type).first()
            trust_factor = source.trust_level if source else 0.80
            svc_conf = nearest_service.confidence_score or 1.0
            confidence_score = round(trust_factor * svc_conf, 2)
        else:
            confidence_score = 0.50

        # Reality Gap: Check citizen reports for this category / area
        reports = (
            db.query(CommunityReport)
            .filter(
                (CommunityReport.area_id == area.id)
                | (CommunityReport.service_id == (nearest_service.id if nearest_service else None))
            )
            .filter(CommunityReport.category_id == category.id)
            .all()
        )

        critical_or_high_reports = [r for r in reports if r.severity in ["critical", "high"]]
        if critical_or_high_reports:
            # Significant divergence detected between official claims and ground reports
            reality_gap_points = 35.0 if any(r.severity == "critical" for r in critical_or_high_reports) else 20.0
            reality_gap_level = "Severe" if any(r.severity == "critical" for r in critical_or_high_reports) else "Moderate"
            divergence_summary = f"{len(critical_or_high_reports)} high/critical citizen report(s) active"
        elif reports:
            reality_gap_points = 10.0
            reality_gap_level = "Minor"
            divergence_summary = f"{len(reports)} community report(s) noted"
        else:
            reality_gap_points = 0.0
            reality_gap_level = "None"
            divergence_summary = "Ground reports align with reported status"

        return {
            "confidence_score": confidence_score,
            "reality_gap_score": reality_gap_points,
            "reality_gap_level": reality_gap_level,
            "reality_gap_summary": divergence_summary,
            "active_reports_count": len(reports),
        }

    # --- 7. Service Desert Classification ---
    def classify_service_desert(self, accessibility_score: float) -> str:
        """
        Exact baseline classification:
        80–100 = Well Served
        60–79  = Adequate
        40–59  = At Risk
        20–39  = Underserved
        0–19   = Critical Desert
        """
        score = round(accessibility_score, 1)
        for min_threshold, label in self.config.desert_classifications:
            if score >= min_threshold:
                return label
        return "Critical Desert"

    # --- 8. Comprehensive Analysis per Area & Category ---
    def analyze_area_category(
        self,
        db: Session,
        area: GeographicArea,
        category: ServiceCategory,
    ) -> Dict[str, Any]:
        """
        Calculates all Stage 3 metrics for a specific geographic area and service category.
        """
        # Area demand and centroid
        demand_population = area.population
        if area.geometry:
            area_lat, area_lon = extract_centroid_lat_lon(area.geometry)
        else:
            area_lat, area_lon = 12.9716, 77.5946

        # Identify nearest/relevant service in category within catchment radius
        services = db.query(Service).filter_by(category_id=category.id).all()
        nearest_service: Optional[Service] = None
        min_dist_km = float("inf")

        for svc in services:
            dist = haversine_distance_km(area_lat, area_lon, svc.latitude, svc.longitude)
            if dist <= self.config.max_catchment_distance_km and dist < min_dist_km:
                min_dist_km = dist
                nearest_service = svc

        # Distance & Travel Time calculation
        if nearest_service:
            travel_data = self.routing.estimate_travel(
                origin_lat=area_lat,
                origin_lon=area_lon,
                dest_lat=nearest_service.latitude,
                dest_lon=nearest_service.longitude,
                mode=self.config.default_travel_mode,
            )
            distance_km = travel_data["direct_distance_km"]
            travel_time_minutes = travel_data["estimated_travel_time_minutes"]
        else:
            distance_km = float("inf")
            travel_time_minutes = float("inf")
            travel_data = {
                "direct_distance_km": None,
                "estimated_travel_time_minutes": None,
                "is_estimate": True,
            }

        # Component scores
        travel_time_score = self.calculate_travel_time_score(travel_time_minutes)
        availability_score = self.calculate_availability_score(nearest_service)
        cap_pres_data = self.calculate_capacity_and_pressure(nearest_service, demand_population)
        capacity_score = cap_pres_data["capacity_score"]
        transport_score = self.calculate_transport_connectivity(db, area_lat, area_lon)

        # Preliminary access for equity calculation
        prelim_access = (
            (travel_time_score * 0.40)
            + (availability_score * 0.30)
            + (capacity_score * 0.30)
        )
        equity_score = self.calculate_equity_score(area, prelim_access)

        # Weighted Accessibility Score
        raw_access = (
            (self.config.travel_time_weight * travel_time_score)
            + (self.config.availability_weight * availability_score)
            + (self.config.capacity_weight * capacity_score)
            + (self.config.transport_weight * transport_score)
            + (self.config.equity_weight * equity_score)
        )
        accessibility_score = round(max(0.0, min(100.0, raw_access)), 1)

        # Gap Score = 100 - Accessibility Score
        gap_score = round(max(0.0, min(100.0, 100.0 - accessibility_score)), 1)

        # Desert classification
        desert_class = self.classify_service_desert(accessibility_score)

        # Confidence & Reality Gap
        conf_gap = self.calculate_confidence_and_reality_gap(db, area, category, nearest_service)

        return {
            "area_id": area.id,
            "area_name": area.name,
            "area_type": area.area_type,
            "category_id": category.id,
            "category_code": category.code,
            "category_name": category.name,
            "nearest_service_id": nearest_service.id if nearest_service else None,
            "nearest_service_name": nearest_service.name if nearest_service else None,
            "nearest_service_status": nearest_service.status if nearest_service else None,
            "distance_km": distance_km if distance_km != float("inf") else None,
            "travel_time_minutes": travel_time_minutes if travel_time_minutes != float("inf") else None,
            "travel_time_score": travel_time_score,
            "availability_score": availability_score,
            "capacity_score": capacity_score,
            "transport_connectivity_score": transport_score,
            "equity_score": equity_score,
            "accessibility_score": accessibility_score,
            "gap_score": gap_score,
            "service_desert_classification": desert_class,
            "service_pressure": cap_pres_data,
            "confidence_score": conf_gap["confidence_score"],
            "reality_gap_score": conf_gap["reality_gap_score"],
            "reality_gap_level": conf_gap["reality_gap_level"],
            "reality_gap_summary": conf_gap["reality_gap_summary"],
        }

    # --- 9. Multi-Category Area Summary ---
    def analyze_area_overall(self, db: Session, area: GeographicArea) -> Dict[str, Any]:
        """
        Runs analytics across all active service categories for an area,
        computing category breakdowns and overall composite scores.
        """
        categories = db.query(ServiceCategory).filter_by(is_active=True).all()
        category_results = []
        total_access = 0.0

        for cat in categories:
            res = self.analyze_area_category(db, area, cat)
            category_results.append(res)
            total_access += res["accessibility_score"]

        avg_access = round(total_access / len(categories), 1) if categories else 0.0
        avg_gap = round(100.0 - avg_access, 1)

        return {
            "area_id": area.id,
            "area_name": area.name,
            "area_type": area.area_type,
            "population": area.population,
            "composite_accessibility_score": avg_access,
            "composite_gap_score": avg_gap,
            "composite_desert_classification": self.classify_service_desert(avg_access),
            "categories_evaluated": len(categories),
            "category_breakdown": category_results,
        }


# Singleton engine instance
default_analytics_engine = AnalyticsEngine()
