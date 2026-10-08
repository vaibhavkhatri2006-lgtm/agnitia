"""
Failure / Resilience Simulation Engine (Stage 4D Task 2) for CivicPulse.
Simulates facility outage/failure in-memory to evaluate systemic resilience,
affected populations, coverage collapse, and single points of failure without DB mutations.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import GeographicArea, ServiceCategory, Service
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.decision.simulation import (
    InterventionSimulationService,
    default_simulation_service,
)


class ResilienceFailureService:
    """
    Evaluates system resilience and vulnerabilities by simulating service unavailability.
    Identifies single points of failure, affected populations, and accessibility drop.
    """

    def __init__(
        self,
        simulation_service: Optional[InterventionSimulationService] = None,
        analytics_engine: Optional[AnalyticsEngine] = None,
    ):
        self.simulation = simulation_service or default_simulation_service
        self.analytics = analytics_engine or default_analytics_engine

    def simulate_service_failure(
        self,
        db: Session,
        service_id: int,
        scope: Optional[str] = "city",
    ) -> Dict[str, Any]:
        """
        Simulates an operational outage of the specified service.
        Runs entirely in-memory without modifying database rows.
        """
        service = db.query(Service).filter_by(id=service_id).first()
        if not service:
            raise ValueError(f"Service with ID {service_id} not found")

        category = service.category
        if not category:
            category = db.query(ServiceCategory).filter_by(id=service.category_id).first()
            if not category:
                raise ValueError(f"Category for service ID {service_id} not found")

        # Locate host area
        location_area = self.simulation.find_target_area(db, service.latitude, service.longitude)

        # Resolve scope areas
        scope_name, areas = self.simulation.resolve_scope_areas(db, scope, location_area)

        # 1. Baseline State (Service operational)
        baseline_scope, baseline_areas = self.simulation.calculate_state_metrics(
            db, areas=areas, category=category, additional_services=None, excluded_service_ids=None
        )

        # 2. Failure State (Service excluded from active network in-memory)
        failure_scope, failure_areas = self.simulation.calculate_state_metrics(
            db, areas=areas, category=category, additional_services=None, excluded_service_ids=[service.id]
        )

        # 3. Measure Resilience Impact
        accessibility_drop = round(
            max(0.0, baseline_scope["accessibility_score"] - failure_scope["accessibility_score"]), 1
        )
        coverage_loss = round(
            max(0.0, baseline_scope["service_coverage"] - failure_scope["service_coverage"]), 1
        )

        directly_affected_pop = 0
        newly_underserved_pop = 0
        affected_areas_list = []

        for area in areas:
            aid = area.id
            b_info = baseline_areas[aid]
            f_info = failure_areas[aid]

            # Check if this service was the primary facility for this area
            orig_metrics = self.analytics.analyze_area_category(db, area, category)
            was_nearest = (orig_metrics.get("nearest_service_id") == service.id)
            if was_nearest:
                directly_affected_pop += area.population

            # Check if area dropped into underserved status
            became_underserved = (b_info["is_covered"] and not f_info["is_covered"])
            if became_underserved:
                newly_underserved_pop += area.population

            area_drop = round(max(0.0, b_info["accessibility_score"] - f_info["accessibility_score"]), 1)

            affected_areas_list.append({
                "area_id": aid,
                "area_name": area.name,
                "population": area.population,
                "before_accessibility": b_info["accessibility_score"],
                "after_accessibility": f_info["accessibility_score"],
                "accessibility_drop": area_drop,
                "before_classification": b_info["service_desert_classification"],
                "after_classification": f_info["service_desert_classification"],
                "was_nearest_service": was_nearest,
                "became_underserved": became_underserved,
            })

        # Resilience Score (0 to 100, 100 = completely resilient system)
        resilience_score = round(
            max(0.0, min(100.0, 100.0 - (accessibility_drop * 1.5 + coverage_loss * 1.5))), 1
        )

        # Single point of failure assessment
        is_spof = bool(coverage_loss >= 15.0 or newly_underserved_pop >= 15000 or accessibility_drop >= 10.0)

        if is_spof:
            criticality_tier = "Critical Infrastructure / Single Point of Failure"
        elif coverage_loss >= 5.0 or newly_underserved_pop >= 5000:
            criticality_tier = "High Dependency"
        elif accessibility_drop >= 3.0:
            criticality_tier = "Moderate Vulnerability"
        else:
            criticality_tier = "Resilient / Redundant"

        # Natural language civic explanation
        impact_phrases = []
        if accessibility_drop > 0:
            impact_phrases.append(f"reduces average accessibility by {accessibility_drop:.1f} points")
        if coverage_loss > 0:
            impact_phrases.append(f"causes {coverage_loss:.1f} percentage points loss in service coverage")
        if newly_underserved_pop > 0:
            impact_phrases.append(f"throws {newly_underserved_pop:,} residents into newly underserved status")
        if directly_affected_pop > 0:
            impact_phrases.append(f"directly disconnects {directly_affected_pop:,} residents who rely on this facility")

        if not impact_phrases:
            summary = "causes negligible network disruption due to robust local service redundancy."
        else:
            summary = "; ".join(impact_phrases) + "."

        explanation = (
            f"Simulated failure of '{service.name}' ({category.name}) in {location_area.name} "
            f"{summary} Systemic resilience rating: {resilience_score}/100 ({criticality_tier})."
        )

        return {
            "service_id": service.id,
            "service_name": service.name,
            "category_code": category.code,
            "category_name": category.name,
            "location_area_name": location_area.name,
            "scope": scope_name,
            "baseline_accessibility": baseline_scope["accessibility_score"],
            "failure_accessibility": failure_scope["accessibility_score"],
            "accessibility_drop": accessibility_drop,
            "baseline_coverage": baseline_scope["service_coverage"],
            "failure_coverage": failure_scope["service_coverage"],
            "coverage_loss": coverage_loss,
            "directly_affected_population": directly_affected_pop,
            "newly_underserved_population": newly_underserved_pop,
            "resilience_score": resilience_score,
            "criticality_tier": criticality_tier,
            "single_point_of_failure": is_spof,
            "explanation": explanation,
            "affected_areas": affected_areas_list,
        }


# Singleton resilience service instance
default_resilience_service = ResilienceFailureService()
