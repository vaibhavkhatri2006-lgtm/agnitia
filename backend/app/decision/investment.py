"""
Investment Priority Engine (Stage 4D Task 1) for CivicPulse.
Calculates transparent deterministic investment priority rankings for civic interventions
based on recommendation scores, affected population, gap severity, equity, and expected impact.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import GeographicArea, ServiceCategory
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.decision.candidates import (
    CandidateLocation,
    CandidateLocationService,
    default_candidate_service,
)
from app.decision.recommendation import (
    RecommendationScoringService,
    default_recommendation_service,
)
from app.decision.simulation import (
    InterventionSimulationService,
    default_simulation_service,
)


class InvestmentPriorityService:
    """
    Computes deterministic investment priority rankings for proposed civic interventions.
    Balances urgency (gap), population scale, equity need, and simulated expected return.
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
        recommendation_service: Optional[RecommendationScoringService] = None,
        simulation_service: Optional[InterventionSimulationService] = None,
        candidate_service: Optional[CandidateLocationService] = None,
        analytics_engine: Optional[AnalyticsEngine] = None,
    ):
        self.recommendation = recommendation_service or default_recommendation_service
        self.simulation = simulation_service or default_simulation_service
        self.candidates = candidate_service or default_candidate_service
        self.analytics = analytics_engine or default_analytics_engine

    def rank_investment_priorities(
        self,
        db: Session,
        service_type: Optional[str] = None,
        min_gap_threshold: float = 20.0,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Scores and ranks candidate interventions across the selected service type
        (or all supported services if service_type is None) into a deterministic priority order.
        """
        # Determine service types to evaluate
        if service_type:
            norm_type = self.recommendation.validate_service_type(service_type)
            eval_services = [norm_type]
        else:
            eval_services = list(self.SUPPORTED_SERVICES)

        all_scored_items: List[Dict[str, Any]] = []

        for st in eval_services:
            rec_result = self.recommendation.rank_candidates(
                db=db,
                service_type=st,
                min_gap_threshold=min_gap_threshold,
            )
            ranked_cands = rec_result["ranked_candidates"]

            for cand_data in ranked_cands:
                cand_id = getattr(cand_data, "candidate_id", None) if not isinstance(cand_data, dict) else cand_data["candidate_id"]
                area_id = getattr(cand_data, "area_id", None) if not isinstance(cand_data, dict) else cand_data["area_id"]
                area_name = getattr(cand_data, "area_name", None) if not isinstance(cand_data, dict) else cand_data["area_name"]
                rec_score = getattr(cand_data, "recommendation_score", None) if not isinstance(cand_data, dict) else cand_data["recommendation_score"]
                factors = getattr(cand_data, "factor_values", None) if not isinstance(cand_data, dict) else cand_data["factor_values"]
                pop = getattr(cand_data, "population", None) if not isinstance(cand_data, dict) else cand_data["population"]
                lat = getattr(cand_data, "latitude", None) if not isinstance(cand_data, dict) else cand_data["latitude"]
                lon = getattr(cand_data, "longitude", None) if not isinstance(cand_data, dict) else cand_data["longitude"]

                gap_sev = factors.get("gap_severity", 50.0)
                norm_pop = factors.get("population_affected", 50.0)
                equity_need = factors.get("equity_need", 50.0)

                # Simulate intervention to calculate expected impact
                try:
                    sim_res = self.simulation.simulate_intervention(
                        db=db,
                        service_type=st,
                        candidate_id=cand_id,
                        scope="city",
                    )
                    impact = sim_res["impact"]
                    target_impact = sim_res["target_area"]
                    target_gain = target_impact.get("accessibility_improvement", 0.0)
                    cov_gain = impact.get("coverage_improvement", 0.0)

                    # Expected impact score (0 to 100)
                    expected_impact_score = round(
                        min(100.0, max(0.0, (target_gain * 0.70) + (cov_gain * 1.50))), 1
                    )
                except Exception:
                    # Safe fallback if simulation encounters edge case
                    target_gain = gap_sev * 0.8
                    expected_impact_score = round(gap_sev * 0.8, 1)

                # Composite Investment Priority Score:
                # 35% Recommendation Score + 25% Expected Impact + 15% Gap + 15% Pop + 10% Equity
                investment_score = (
                    (rec_score * 0.35)
                    + (expected_impact_score * 0.25)
                    + (gap_sev * 0.15)
                    + (norm_pop * 0.15)
                    + (equity_need * 0.10)
                )
                investment_score = round(max(0.0, min(100.0, investment_score)), 1)

                # Priority Tier assignment
                if investment_score >= 80.0:
                    priority_tier = "Highest Priority"
                elif investment_score >= 65.0:
                    priority_tier = "High Priority"
                elif investment_score >= 50.0:
                    priority_tier = "Moderate Priority"
                else:
                    priority_tier = "Low Priority"

                # Driver identification
                primary_drivers = []
                if gap_sev >= 70.0:
                    primary_drivers.append("critical_service_gap")
                if expected_impact_score >= 70.0:
                    primary_drivers.append("high_accessibility_impact")
                if pop >= 15000:
                    primary_drivers.append("large_beneficiary_population")
                if equity_need >= 50.0:
                    primary_drivers.append("socioeconomic_equity_need")
                if not primary_drivers:
                    primary_drivers.append("balanced_civic_return")

                # Natural language rationale
                rationale = (
                    f"Strategic investment in {area_name}: addresses severe {st} deficit ({gap_sev:.1f}% gap), "
                    f"serves {pop:,} residents with expected accessibility gain of +{target_gain:.1f} points "
                    f"and strong recommendation alignment ({rec_score:.1f}/100)."
                )

                all_scored_items.append({
                    "candidate_id": cand_id,
                    "service_type": st,
                    "area_id": area_id,
                    "area_name": area_name,
                    "latitude": lat,
                    "longitude": lon,
                    "investment_priority_score": investment_score,
                    "priority_tier": priority_tier,
                    "recommendation_score": rec_score,
                    "expected_impact_score": expected_impact_score,
                    "population_affected": pop,
                    "gap_severity": gap_sev,
                    "equity_need": equity_need,
                    "estimated_cost_tier": "Standard Civic Facility (Tier 1)",
                    "rationale": rationale,
                    "primary_drivers": primary_drivers,
                })

        # Deterministic sorting:
        # Primary: investment_priority_score DESC
        # Secondary: population_affected DESC
        # Tertiary: candidate_id ASC
        all_scored_items.sort(
            key=lambda x: (-x["investment_priority_score"], -x["population_affected"], x["candidate_id"])
        )

        # Assign sequential rank 1, 2, 3...
        ranked_investments = []
        for idx, item in enumerate(all_scored_items[:max_results], start=1):
            item_copy = dict(item)
            item_copy["rank"] = idx
            ranked_investments.append(item_copy)

        return {
            "service_type": service_type,
            "total_interventions_evaluated": len(all_scored_items),
            "ranked_investments": ranked_investments,
        }


# Singleton investment service
default_investment_service = InvestmentPriorityService()
