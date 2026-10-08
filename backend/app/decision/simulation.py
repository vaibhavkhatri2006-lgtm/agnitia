"""
What-If / Intervention Simulation Engine (Stage 4C) for CivicPulse.
Simulates adding proposed civic facilities in-memory without permanently modifying official data.
Calculates Before vs After metrics, measurable impact, and explanations.
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from shapely.geometry import Point
from shapely import wkt

from app.models import GeographicArea, ServiceCategory, Service, ServiceCapacity
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.analytics.distance import (
    haversine_distance_km,
    extract_centroid_lat_lon,
    default_routing_provider,
    RoutingProvider,
)
from app.decision.candidates import (
    CandidateLocation,
    CandidateLocationService,
    default_candidate_service,
)


class InterventionSimulationService:
    """
    Core engine that executes deterministic what-if simulations of civic interventions.
    Compares baseline service access against simulated post-intervention access without
    writing to the database.
    """

    SUPPORTED_SERVICES = [
        "healthcare",
        "education",
        "transport",
        "water",
        "market",
    ]

    def __init__(
        self,
        analytics_engine: Optional[AnalyticsEngine] = None,
        candidate_service: Optional[CandidateLocationService] = None,
        routing_provider: Optional[RoutingProvider] = None,
    ):
        self.analytics = analytics_engine or default_analytics_engine
        self.candidate_service = candidate_service or default_candidate_service
        self.routing = routing_provider or default_routing_provider

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

    # --- 2. Coordinate Validation ---
    def validate_coordinates(self, latitude: Any, longitude: Any) -> Tuple[float, float]:
        """
        Validates latitude and longitude ranges and finite numeric representation.
        Raises ValueError if invalid.
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
        except (TypeError, ValueError):
            raise ValueError("Coordinates must be valid numeric numbers")

        if math.isnan(lat) or math.isinf(lat) or math.isnan(lon) or math.isinf(lon):
            raise ValueError("Coordinates cannot be NaN or infinite")

        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} out of valid bounds [-90.0, 90.0]")

        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} out of valid bounds [-180.0, 180.0]")

        return lat, lon

    # --- 3. Target Area Resolution ---
    def find_target_area(
        self,
        db: Session,
        latitude: float,
        longitude: float,
    ) -> GeographicArea:
        """
        Identifies the geographic neighbourhood containing the given coordinates.
        Falls back to the nearest neighbourhood by centroid distance if not strictly inside.
        """
        neighbourhoods = (
            db.query(GeographicArea)
            .filter_by(area_type="neighbourhood")
            .order_by(GeographicArea.id)
            .all()
        )
        if not neighbourhoods:
            # Fallback to any geographic areas
            neighbourhoods = db.query(GeographicArea).order_by(GeographicArea.id).all()
            if not neighbourhoods:
                raise ValueError("No geographic areas available in database")

        pt = Point(longitude, latitude)

        # 1. Exact polygon containment
        for area in neighbourhoods:
            if area.geometry:
                try:
                    poly = wkt.loads(area.geometry)
                    if poly.contains(pt) or poly.covers(pt):
                        return area
                except Exception:
                    pass

        # 2. Nearest centroid fallback
        best_area = neighbourhoods[0]
        min_dist = float("inf")
        for area in neighbourhoods:
            if area.geometry:
                c_lat, c_lon = extract_centroid_lat_lon(area.geometry)
            else:
                c_lat, c_lon = 12.9716, 77.5946
            dist = haversine_distance_km(latitude, longitude, c_lat, c_lon)
            if dist < min_dist:
                min_dist = dist
                best_area = area

        return best_area

    # --- 4. Location & Candidate Resolution ---
    def resolve_intervention_location(
        self,
        db: Session,
        service_type: str,
        candidate_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Tuple[float, float, GeographicArea, Optional[str]]:
        """
        Resolves input coordinates or candidate ID into (lat, lon, target_area, candidate_id).
        Validates candidate ID validity and coordinate constraints.
        """
        if candidate_id:
            # Look up candidate
            candidates = self.candidate_service.generate_candidates_for_service(
                db, service_type=service_type, include_rejected=True
            )
            matched = next((c for c in candidates if c.candidate_id == candidate_id), None)
            if not matched:
                raise ValueError(
                    f"Candidate '{candidate_id}' not found for service type '{service_type}'"
                )

            if matched.validity_status == "rejected":
                raise ValueError(
                    f"Candidate '{candidate_id}' is invalid: {matched.rejection_reason}"
                )

            area = db.query(GeographicArea).filter_by(id=matched.area_id).first()
            if not area:
                area = self.find_target_area(db, matched.latitude, matched.longitude)

            return matched.latitude, matched.longitude, area, matched.candidate_id

        elif latitude is not None and longitude is not None:
            lat, lon = self.validate_coordinates(latitude, longitude)
            target_area = self.find_target_area(db, lat, lon)
            return lat, lon, target_area, None

        else:
            raise ValueError(
                "Either 'candidate_id' or both 'latitude' and 'longitude' must be provided"
            )

    # --- 5. Scope Resolution ---
    def resolve_scope_areas(
        self,
        db: Session,
        scope: Optional[str],
        target_area: GeographicArea,
    ) -> Tuple[str, List[GeographicArea]]:
        """
        Resolves the list of areas to evaluate based on scope.
        Defaults to city-wide non-overlapping neighbourhoods.
        """
        norm_scope = (scope or "city").strip().lower()

        if norm_scope in ["city", "all", "neighbourhoods", "citywide"]:
            areas = (
                db.query(GeographicArea)
                .filter_by(area_type="neighbourhood")
                .order_by(GeographicArea.id)
                .all()
            )
            if not areas:
                areas = db.query(GeographicArea).order_by(GeographicArea.id).all()
            return "city", areas

        if norm_scope in ["local", "target", "target_area"]:
            return f"area_{target_area.id}", [target_area]

        # Check if numeric area ID
        if norm_scope.isdigit():
            aid = int(norm_scope)
            area = db.query(GeographicArea).filter_by(id=aid).first()
            if not area:
                raise ValueError(f"Analysis scope area ID '{aid}' not found")
            return f"area_{aid}", [area]

        # Named area match
        named_area = db.query(GeographicArea).filter(GeographicArea.name.ilike(scope)).first()
        if named_area:
            return f"area_{named_area.id}", [named_area]

        # Default fallback to city
        areas = (
            db.query(GeographicArea)
            .filter_by(area_type="neighbourhood")
            .order_by(GeographicArea.id)
            .all()
        )
        return "city", areas

    # --- 6. Estimate Travel Time when Outside Catchment ---
    def _estimate_travel_time_for_area(
        self,
        area_lat: float,
        area_lon: float,
        all_services: List[Service],
    ) -> float:
        """
        Calculates deterministic travel time (minutes) to the closest available facility
        anywhere in the system, ensuring finite metrics even for underserved areas.
        """
        if not all_services:
            return 60.0  # standard unserviced baseline

        min_dist_km = float("inf")
        for svc in all_services:
            dist = haversine_distance_km(area_lat, area_lon, svc.latitude, svc.longitude)
            if dist < min_dist_km:
                min_dist_km = dist

        # Walking estimate at 4.5 km/h with 1.3 urban circuity factor
        walking_mins = (min_dist_km / 4.5) * 60.0 * 1.3
        return round(max(3.0, min(120.0, walking_mins)), 1)

    # --- 7. State Metrics Calculation (Before & After) ---
    def calculate_state_metrics(
        self,
        db: Session,
        areas: List[GeographicArea],
        category: ServiceCategory,
        additional_services: Optional[List[Service]] = None,
        excluded_service_ids: Optional[List[int]] = None,
    ) -> Tuple[Dict[str, Any], Dict[int, Dict[str, Any]]]:
        """
        Computes aggregate metrics across the scope and returns per-area details.
        Supports optional in-memory additional_services and failure excluded_service_ids.
        """
        # Gather all active services for global travel time approximation
        db_services = db.query(Service).filter_by(category_id=category.id).all()
        if excluded_service_ids:
            db_services = [s for s in db_services if s.id not in excluded_service_ids]
        combined_services = list(db_services)
        if additional_services:
            matching = [
                s for s in additional_services
                if s.category_id == category.id and (not excluded_service_ids or s.id not in excluded_service_ids)
            ]
            combined_services += matching

        total_population = sum(a.population for a in areas)
        if total_population == 0:
            total_population = 1  # prevent division by zero

        weighted_access_sum = 0.0
        weighted_travel_time_sum = 0.0
        covered_population = 0
        underserved_population = 0
        area_details: Dict[int, Dict[str, Any]] = {}

        for area in areas:
            metrics = self.analytics.analyze_area_category(
                db,
                area,
                category,
                additional_services=additional_services,
                excluded_service_ids=excluded_service_ids,
            )
            area_id = area.id
            pop = area.population

            # Calculate travel time (using catchment travel time or closest facility estimate)
            if metrics["travel_time_minutes"] is not None:
                tt = float(metrics["travel_time_minutes"])
            else:
                if area.geometry:
                    c_lat, c_lon = extract_centroid_lat_lon(area.geometry)
                else:
                    c_lat, c_lon = 12.9716, 77.5946
                tt = self._estimate_travel_time_for_area(c_lat, c_lon, combined_services)

            weighted_access_sum += metrics["accessibility_score"] * pop
            weighted_travel_time_sum += tt * pop

            # Desert & Coverage determination:
            # An area is covered if accessibility >= 60.0 (Adequate or Well Served)
            is_covered = (
                metrics["service_desert_classification"] in ["Well Served", "Adequate"]
                or metrics["accessibility_score"] >= 60.0
            )

            if is_covered:
                covered_population += pop
            else:
                underserved_population += pop

            area_details[area_id] = {
                "area_id": area_id,
                "area_name": area.name,
                "area_type": area.area_type,
                "population": pop,
                "accessibility_score": metrics["accessibility_score"],
                "gap_score": metrics["gap_score"],
                "service_desert_classification": metrics["service_desert_classification"],
                "travel_time_minutes": tt,
                "distance_km": metrics["distance_km"],
                "is_covered": is_covered,
            }

        avg_access = round(weighted_access_sum / total_population, 1)
        avg_gap = round(max(0.0, min(100.0, 100.0 - avg_access)), 1)
        coverage_pct = round((covered_population / total_population) * 100.0, 1)
        avg_travel_time = round(weighted_travel_time_sum / total_population, 1)

        scope_metrics = {
            "accessibility_score": avg_access,
            "gap_score": avg_gap,
            "service_coverage": coverage_pct,
            "underserved_population": underserved_population,
            "average_travel_time_minutes": avg_travel_time,
        }

        return scope_metrics, area_details

    # --- 8. Impact Calculation ---
    def calculate_impact(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        target_area_before: Dict[str, Any],
        target_area_after: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculates the delta between before and after states.
        Guarantees non-negative impact values and safety protection.
        """
        access_improvement = round(
            max(0.0, after["accessibility_score"] - before["accessibility_score"]), 1
        )
        gap_reduction = round(
            max(0.0, before["gap_score"] - after["gap_score"]), 1
        )
        coverage_improvement = round(
            max(0.0, after["service_coverage"] - before["service_coverage"]), 1
        )
        underserved_reduction = max(
            0, before["underserved_population"] - after["underserved_population"]
        )

        # Population gaining access
        if underserved_reduction > 0:
            pop_gaining = underserved_reduction
        elif not target_area_before["is_covered"] and target_area_after["is_covered"]:
            pop_gaining = target_area_before["population"]
        else:
            pop_gaining = 0

        travel_time_saved = round(
            max(0.0, before["average_travel_time_minutes"] - after["average_travel_time_minutes"]), 1
        )

        return {
            "accessibility_improvement": access_improvement,
            "gap_reduction": gap_reduction,
            "coverage_improvement": coverage_improvement,
            "underserved_population_reduction": underserved_reduction,
            "population_gaining_access": pop_gaining,
            "travel_time_improvement_minutes": travel_time_saved,
        }

    # --- 9. Explanation Generation ---
    def generate_explanation(
        self,
        service_type: str,
        target_area: GeographicArea,
        target_before: Dict[str, Any],
        target_after: Dict[str, Any],
        impact: Dict[str, Any],
        proposed_capacity: int,
    ) -> Tuple[str, List[str]]:
        """
        Builds a natural language civic explanation and returns key improvement factors.
        """
        reasons = []
        factors = []

        area_name = target_area.name
        pop = target_area.population

        # Travel time factor
        tt_before = target_before["travel_time_minutes"]
        tt_after = target_after["travel_time_minutes"]
        if tt_before is not None and tt_after is not None and tt_before > tt_after:
            saved = round(tt_before - tt_after, 1)
            reasons.append(f"reduces estimated travel time from {tt_before:.1f} to {tt_after:.1f} minutes ({saved:.1f} min saved)")
            factors.append("travel_time_reduction")

        # Desert / Gap resolution factor
        if (
            target_before["service_desert_classification"] in ["Critical Desert", "Underserved"]
            and target_after["service_desert_classification"] not in ["Critical Desert", "Underserved"]
        ):
            reasons.append(f"resolves the {target_before['service_desert_classification']} status in {area_name}")
            factors.append("service_desert_resolution")

        # Underserved population relief
        if impact["underserved_population_reduction"] > 0:
            reasons.append(f"provides meaningful {service_type} coverage for {impact['underserved_population_reduction']:,} previously underserved residents")
            factors.append("underserved_population_relief")
        elif not target_before["is_covered"]:
            reasons.append(f"serves a community of {pop:,} residents with high baseline access need")
            factors.append("underserved_population_relief")

        # Coverage expansion
        if impact["coverage_improvement"] > 0:
            reasons.append(f"increases overall service coverage by +{impact['coverage_improvement']:.1f} percentage points")
            factors.append("coverage_expansion")

        # Capacity addition
        if proposed_capacity > 0:
            reasons.append(f"adds {proposed_capacity:,} units of dedicated capacity relieving service pressure")
            factors.append("capacity_addition")

        # Ensure at least basic factors if changes were small
        if not factors:
            factors.append("accessibility_maintenance")
            reasons.append(f"maintains adequate {service_type} accessibility across the locality")

        explanation = (
            f"The proposed {service_type} facility in {area_name} improves access because it "
            + "; ".join(reasons)
            + "."
        )

        return explanation, factors

    # --- 10. Main Simulation Execution ---
    def simulate_intervention(
        self,
        db: Session,
        service_type: str,
        candidate_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        scope: Optional[str] = "city",
        proposed_name: Optional[str] = None,
        proposed_capacity: Optional[int] = 5000,
    ) -> Dict[str, Any]:
        """
        Executes an in-memory what-if intervention simulation.
        Does NOT modify the official database.
        """
        # 1. Validate Service Type
        norm_service = self.validate_service_type(service_type)
        category = db.query(ServiceCategory).filter_by(code=norm_service).first()
        if not category:
            raise ValueError(f"Service category '{norm_service}' not found in database")

        # 2. Resolve Intervention Location & Target Area
        lat, lon, target_area, resolved_candidate_id = self.resolve_intervention_location(
            db,
            service_type=norm_service,
            candidate_id=candidate_id,
            latitude=latitude,
            longitude=longitude,
        )

        # 3. Resolve Scope Areas
        scope_name, areas = self.resolve_scope_areas(db, scope, target_area)

        # 4. Calculate BEFORE State
        before_scope, before_areas = self.calculate_state_metrics(
            db, areas=areas, category=category, additional_services=None
        )

        target_before = before_areas.get(target_area.id)
        if not target_before:
            # Evaluate target area explicitly if not in scope areas
            _, target_single = self.calculate_state_metrics(
                db, areas=[target_area], category=category, additional_services=None
            )
            target_before = target_single[target_area.id]

        # 5. Build IN-MEMORY Simulated Service (NEVER ADDED TO DB SESSION)
        facility_capacity = max(1, proposed_capacity or 5000)
        facility_name = proposed_name or f"Simulated {category.name} Facility ({target_area.name})"

        simulated_service = Service(
            id=-1,
            name=facility_name,
            category_id=category.id,
            latitude=lat,
            longitude=lon,
            status="operational",
            source_type="simulation",
            confidence_score=0.90,
        )
        simulated_service.capacity_record = ServiceCapacity(
            id=-1,
            service_id=-1,
            capacity=facility_capacity,
            current_load=0,
        )

        # 6. Calculate AFTER State
        after_scope, after_areas = self.calculate_state_metrics(
            db, areas=areas, category=category, additional_services=[simulated_service]
        )

        target_after = after_areas.get(target_area.id)
        if not target_after:
            _, target_single = self.calculate_state_metrics(
                db, areas=[target_area], category=category, additional_services=[simulated_service]
            )
            target_after = target_single[target_area.id]

        # 7. Calculate Impact
        impact = self.calculate_impact(
            before=before_scope,
            after=after_scope,
            target_area_before=target_before,
            target_area_after=target_after,
        )

        # 8. Target Area Summary
        tt_before = target_before["travel_time_minutes"]
        tt_after = target_after["travel_time_minutes"]
        tt_saved = round(max(0.0, (tt_before or 0.0) - (tt_after or 0.0)), 1) if tt_before else None

        target_impact = {
            "area_id": target_area.id,
            "area_name": target_area.name,
            "area_type": target_area.area_type,
            "population": target_area.population,
            "before_accessibility": target_before["accessibility_score"],
            "after_accessibility": target_after["accessibility_score"],
            "accessibility_improvement": round(
                max(0.0, target_after["accessibility_score"] - target_before["accessibility_score"]), 1
            ),
            "before_gap": target_before["gap_score"],
            "after_gap": target_after["gap_score"],
            "before_classification": target_before["service_desert_classification"],
            "after_classification": target_after["service_desert_classification"],
            "before_travel_time_minutes": tt_before,
            "after_travel_time_minutes": tt_after,
            "travel_time_saved_minutes": tt_saved,
        }

        # 9. Explanation & Factors
        explanation, primary_factors = self.generate_explanation(
            service_type=norm_service,
            target_area=target_area,
            target_before=target_before,
            target_after=target_after,
            impact=impact,
            proposed_capacity=facility_capacity,
        )

        # Deterministic simulation run identifier
        cand_key = resolved_candidate_id or f"{round(lat, 4)}_{round(lon, 4)}"
        sim_id = f"sim-{norm_service}-{cand_key}-{scope_name}"

        return {
            "simulation_id": sim_id,
            "service_type": norm_service,
            "candidate_id": resolved_candidate_id,
            "latitude": lat,
            "longitude": lon,
            "scope": scope_name,
            "target_area": target_impact,
            "before": before_scope,
            "after": after_scope,
            "impact": impact,
            "explanation": explanation,
            "primary_factors": primary_factors,
            "confidence": 0.90,
        }

    # --- 11. Multi-Scenario Comparison (Stage 9 Scenario Lab) ---
    def compare_scenarios(
        self,
        db: Session,
        service_type: str,
        scope: Optional[str] = "city",
        scenarios: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Compares multiple intervention scenarios:
        - Baseline: Current state (0 facilities added)
        - Scenario 1: One new facility (top recommended candidate or custom)
        - Scenario 2+: Multiple facilities (top 2+ candidates or custom)
        Returns consistent, deterministic metrics for each scenario without modifying official data.
        """
        norm_service = self.validate_service_type(service_type)
        category = db.query(ServiceCategory).filter_by(code=norm_service).first()
        if not category:
            raise ValueError(f"Service category '{norm_service}' not found in database")

        scope_name, areas = self.resolve_scope_areas(db, scope, None)
        total_population = sum(a.population for a in areas)

        # 1. Baseline state (Current State)
        baseline_metrics, _ = self.calculate_state_metrics(
            db, areas=areas, category=category, additional_services=None
        )

        baseline_item = {
            "scenario_id": "baseline",
            "name": "Current State",
            "description": "Baseline municipal infrastructure without additional facilities",
            "facilities_added": 0,
            "metrics": baseline_metrics,
            "impact_vs_baseline": {
                "accessibility_improvement": 0.0,
                "gap_reduction": 0.0,
                "coverage_improvement": 0.0,
                "underserved_population_reduction": 0,
                "travel_time_saved_minutes": 0.0,
            },
        }

        # 2. Determine scenarios to evaluate
        scenario_results = [baseline_item]
        best_scenario_id = "baseline"
        best_gain = -1.0

        if not scenarios:
            # Generate default 1-facility and 2-facility scenarios from top candidates
            valid_cands = self.candidate_service.generate_candidates_for_service(
                db, service_type=norm_service, include_rejected=False
            )
            scenario_specs = []
            if len(valid_cands) >= 1:
                scenario_specs.append({
                    "scenario_id": "single_facility",
                    "name": f"1 New Facility ({valid_cands[0].area_name})",
                    "description": f"Add primary proposed facility at {valid_cands[0].candidate_id}",
                    "facilities": [{"candidate_id": valid_cands[0].candidate_id}],
                })
            if len(valid_cands) >= 2:
                scenario_specs.append({
                    "scenario_id": "two_facilities",
                    "name": f"2 New Facilities ({valid_cands[0].area_name} + {valid_cands[1].area_name})",
                    "description": "Add 2 top prioritized facilities simultaneously",
                    "facilities": [
                        {"candidate_id": valid_cands[0].candidate_id},
                        {"candidate_id": valid_cands[1].candidate_id},
                    ],
                })
        else:
            scenario_specs = scenarios

        # 3. Simulate each scenario in-memory
        for sc in scenario_specs:
            sc_id = sc.get("scenario_id") if isinstance(sc, dict) else getattr(sc, "scenario_id", "custom_scenario")
            if sc_id == "baseline":
                continue

            simulated_services: List[Service] = []
            fac_inputs = sc.get("facilities", []) if isinstance(sc, dict) else getattr(sc, "facilities", [])
            for idx, fac in enumerate(fac_inputs, start=1):
                cand_id = fac.get("candidate_id") if isinstance(fac, dict) else getattr(fac, "candidate_id", None)
                lat_in = fac.get("latitude") if isinstance(fac, dict) else getattr(fac, "latitude", None)
                lon_in = fac.get("longitude") if isinstance(fac, dict) else getattr(fac, "longitude", None)
                cap_in = fac.get("proposed_capacity") if isinstance(fac, dict) else getattr(fac, "proposed_capacity", 5000)
                name_in = fac.get("proposed_name") if isinstance(fac, dict) else getattr(fac, "proposed_name", None)

                lat, lon, target_area, res_cand_id = self.resolve_intervention_location(
                    db,
                    service_type=norm_service,
                    candidate_id=cand_id,
                    latitude=lat_in,
                    longitude=lon_in,
                )

                fac_cap = max(1, cap_in or 5000)
                fac_name = name_in or f"Simulated {category.name} #{idx} ({target_area.name})"
                sim_svc = Service(
                    id=-(idx + 100),
                    name=fac_name,
                    category_id=category.id,
                    latitude=lat,
                    longitude=lon,
                    status="operational",
                    source_type="simulation",
                    confidence_score=0.90,
                )
                sim_svc.capacity_record = ServiceCapacity(
                    id=-(idx + 100),
                    service_id=-(idx + 100),
                    capacity=fac_cap,
                    current_load=0,
                )
                simulated_services.append(sim_svc)

            # Recalculate metrics with all simulated facilities
            after_metrics, _ = self.calculate_state_metrics(
                db, areas=areas, category=category, additional_services=simulated_services
            )

            access_gain = round(max(0.0, after_metrics["accessibility_score"] - baseline_metrics["accessibility_score"]), 1)
            gap_red = round(max(0.0, baseline_metrics["gap_score"] - after_metrics["gap_score"]), 1)
            cov_gain = round(max(0.0, after_metrics["service_coverage"] - baseline_metrics["service_coverage"]), 1)
            underserved_red = max(0, baseline_metrics["underserved_population"] - after_metrics["underserved_population"])
            tt_saved = round(max(0.0, baseline_metrics["average_travel_time_minutes"] - after_metrics["average_travel_time_minutes"]), 1)

            sc_name = sc.get("name") if isinstance(sc, dict) else getattr(sc, "name", sc_id)
            sc_desc = sc.get("description") if isinstance(sc, dict) else getattr(sc, "description", None)

            sc_result = {
                "scenario_id": sc_id,
                "name": sc_name,
                "description": sc_desc,
                "facilities_added": len(simulated_services),
                "metrics": after_metrics,
                "impact_vs_baseline": {
                    "accessibility_improvement": access_gain,
                    "gap_reduction": gap_red,
                    "coverage_improvement": cov_gain,
                    "underserved_population_reduction": underserved_red,
                    "travel_time_saved_minutes": tt_saved,
                },
            }
            scenario_results.append(sc_result)

            if access_gain > best_gain:
                best_gain = access_gain
                best_scenario_id = sc_id

        summary_text = (
            f"Compared {len(scenario_results)} infrastructure scenarios for {category.name}. "
            f"Highest access enhancement achieved by scenario '{best_scenario_id}' (+{max(0.0, best_gain):.1f} points)."
        )

        return {
            "service_type": norm_service,
            "scope": scope_name,
            "total_population": total_population,
            "baseline": baseline_item,
            "scenarios": scenario_results,
            "best_scenario_id": best_scenario_id,
            "summary": summary_text,
            "is_simulated": True,
            "label": "Scenario Lab - Multi-Facility Intervention Comparison",
        }


# Singleton simulation service instance
default_simulation_service = InterventionSimulationService()

