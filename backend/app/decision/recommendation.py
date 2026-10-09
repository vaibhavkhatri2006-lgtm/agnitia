"""
Recommendation Scoring Engine (Stage 4B) for CivicPulse.
Scores, explains, and ranks candidate intervention locations deterministically.
"""
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.models import GeographicArea, ServiceCategory
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.decision.candidates import (
    CandidateLocation,
    CandidateLocationService,
    default_candidate_service,
)


class RecommendationConfig(BaseModel):
    """
    Central, validated configuration for the Recommendation Scoring Engine.
    All factor weights must sum to 1.0 (100%).
    """
    gap_weight: float = Field(0.30, ge=0.0, le=1.0, description="Weight for gap severity (30%)")
    population_weight: float = Field(0.25, ge=0.0, le=1.0, description="Weight for population affected (25%)")
    travel_need_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for travel-time need (15%)")
    capacity_pressure_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for capacity pressure (10%)")
    equity_need_weight: float = Field(0.10, ge=0.0, le=1.0, description="Weight for equity need (10%)")
    connectivity_weight: float = Field(0.05, ge=0.0, le=1.0, description="Weight for transport connectivity (5%)")
    confidence_weight: float = Field(0.05, ge=0.0, le=1.0, description="Weight for data confidence (5%)")
    reference_population: float = Field(25000.0, gt=0.0, description="Reference population scale for normalization")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "RecommendationConfig":
        total = (
            self.gap_weight
            + self.population_weight
            + self.travel_need_weight
            + self.capacity_pressure_weight
            + self.equity_need_weight
            + self.connectivity_weight
            + self.confidence_weight
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Recommendation factor weights must sum to 1.0 (100%). Current sum: {total:.4f}"
            )
        return self


default_recommendation_config = RecommendationConfig()


class ScoredCandidate:
    """Represents a candidate location that has received a recommendation priority score."""

    def __init__(
        self,
        candidate: CandidateLocation,
        recommendation_score: float,
        rank: int,
        factor_values: Dict[str, float],
        factor_weights: Dict[str, float],
        reasons: List[str],
        confidence: float,
    ):
        self.candidate = candidate
        self.candidate_id = candidate.candidate_id
        self.service_type = candidate.service_type
        self.recommendation_score = recommendation_score
        self.rank = rank
        self.latitude = candidate.latitude
        self.longitude = candidate.longitude
        self.area_id = candidate.area_id
        self.area_name = candidate.area_name
        self.population = candidate.population
        self.strategy = candidate.strategy
        self.confidence = confidence
        self.factor_values = factor_values
        self.factor_weights = factor_weights
        self.reasons = reasons

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "service_type": self.service_type,
            "rank": self.rank,
            "recommendation_score": self.recommendation_score,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_id": self.area_id,
            "area_name": self.area_name,
            "population": self.population,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "factor_values": self.factor_values,
            "factor_weights": self.factor_weights,
            "reasons": self.reasons,
        }


class RecommendationScoringService:
    """
    Core engine that normalizes factors, scores candidates, assigns ranks,
    and constructs explanatory civic justifications.
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
        config: Optional[RecommendationConfig] = None,
        candidate_service: Optional[CandidateLocationService] = None,
        analytics_engine: Optional[AnalyticsEngine] = None,
    ):
        self.config = config or default_recommendation_config
        self.candidates = candidate_service or default_candidate_service
        self.analytics = analytics_engine or default_analytics_engine

    # --- 1. Service Type Validation ---
    def validate_service_type(self, service_type: str) -> str:
        """Validates that the service type is supported."""
        if not service_type or not isinstance(service_type, str):
            raise ValueError(
                f"Service type must be a non-empty string. Supported: {', '.join(self.SUPPORTED_SERVICES)}"
            )
        norm = service_type.strip().lower()
        if norm not in self.SUPPORTED_SERVICES:
            raise ValueError(
                f"Unsupported service type '{service_type}'. Supported: {', '.join(self.SUPPORTED_SERVICES)}"
            )
        return norm

    # --- 2. Factor Normalization (Strictly 0.0 - 100.0) ---
    def normalize_gap_severity(self, gap_score: Optional[float]) -> float:
        """Normalizes gap score to 0–100."""
        if gap_score is None:
            return 50.0
        return round(max(0.0, min(100.0, float(gap_score))), 1)

    def normalize_population_affected(
        self,
        population: Optional[int],
        ref_population: Optional[float] = None,
    ) -> float:
        """Normalizes population to 0–100 using reference population scale."""
        if population is None or population <= 0:
            return 0.0
        scale = ref_population or self.config.reference_population
        norm = (float(population) / scale) * 100.0
        return round(max(0.0, min(100.0, norm)), 1)

    def normalize_travel_time_need(self, travel_time_score: Optional[float]) -> float:
        """
        Converts travel-time score into Travel-Time Need (0-100).
        Lower travel access (or unreached) = Higher travel need.
        """
        if travel_time_score is None:
            # No reachable facility in catchment -> 100% need
            return 100.0
        score = max(0.0, min(100.0, float(travel_time_score)))
        return round(100.0 - score, 1)

    def normalize_capacity_pressure(
        self,
        capacity_score: Optional[float],
        pressure_category: Optional[str] = None,
    ) -> float:
        """
        Normalizes capacity pressure to 0–100.
        Critical/overloaded = 100, High = 75, Moderate = 50, Low = 20.
        """
        if pressure_category:
            cat = pressure_category.lower().strip()
            cat_map = {
                "critical": 100.0,
                "high": 75.0,
                "moderate": 50.0,
                "low": 20.0,
            }
            if cat in cat_map:
                return cat_map[cat]

        if capacity_score is None:
            return 50.0

        # Invert capacity score: 0 capacity score = 100 pressure
        cap = max(0.0, min(100.0, float(capacity_score)))
        return round(100.0 - cap, 1)

    def normalize_equity_need(self, equity_score: Optional[float]) -> float:
        """Normalizes equity need to 0–100."""
        if equity_score is None:
            return 50.0
        # Equity score reflects baseline demographic vulnerability
        return round(max(0.0, min(100.0, float(equity_score))), 1)

    def normalize_connectivity(self, transport_score: Optional[float]) -> float:
        """Normalizes transit connectivity to 0–100."""
        if transport_score is None:
            return 50.0
        return round(max(0.0, min(100.0, float(transport_score))), 1)

    def normalize_data_confidence(self, confidence_score: Optional[float]) -> float:
        """Normalizes data confidence to 0–100."""
        if confidence_score is None:
            return 50.0
        conf = float(confidence_score)
        if conf <= 1.0:
            conf = conf * 100.0
        return round(max(0.0, min(100.0, conf)), 1)

    # --- 3. Explanation Generator ---
    def generate_explanations(
        self,
        service_type: str,
        factors: Dict[str, float],
        population: int,
        area_name: str,
    ) -> List[str]:
        """Generates clear, human-readable reasons for a candidate's score."""
        reasons: List[str] = []

        # Gap
        gap = factors["gap_severity"]
        if gap >= 70.0:
            reasons.append(f"Severe {service_type} accessibility gap ({gap:.1f}%) in {area_name}")
        elif gap >= 40.0:
            reasons.append(f"Moderate {service_type} access gap ({gap:.1f}%)")
        else:
            reasons.append(f"Low access deficit ({gap:.1f}%)")

        # Population
        pop_fac = factors["population_affected"]
        if pop_fac >= 60.0:
            reasons.append(f"Large affected population ({population:,} residents)")
        elif pop_fac >= 30.0:
            reasons.append(f"Substantial community base ({population:,} residents)")
        else:
            reasons.append(f"Local neighborhood population ({population:,} residents)")

        # Travel Need
        travel = factors["travel_time_need"]
        if travel >= 75.0:
            reasons.append("Long estimated travel time with no reachable facility in catchment")
        elif travel >= 40.0:
            reasons.append("Elevated travel time to nearest alternative facility")
        else:
            reasons.append("Proximity to existing alternatives is relatively accessible")

        # Capacity Pressure
        pressure = factors["capacity_pressure"]
        if pressure >= 75.0:
            reasons.append("Limited nearby capacity with critical service load pressure")
        elif pressure >= 40.0:
            reasons.append("Moderate facility capacity constraints in surrounding zone")
        else:
            reasons.append("Existing service load is within manageable capacity")

        # Equity
        equity = factors["equity_need"]
        if equity >= 60.0:
            reasons.append("High equity need and demographic vulnerability prioritization")

        # Connectivity
        conn = factors["connectivity"]
        if conn >= 60.0:
            reasons.append("Strong transit connectivity supporting regional catchment")

        return reasons

    # --- 4. Single Candidate Scoring ---
    def score_candidate(
        self,
        candidate: CandidateLocation,
        metrics: Dict[str, Any],
        config: Optional[RecommendationConfig] = None,
    ) -> ScoredCandidate:
        """Calculates normalized factors and composite recommendation score for a candidate."""
        cfg = config or self.config

        pressure_cat = None
        if "service_pressure" in metrics and isinstance(metrics["service_pressure"], dict):
            pressure_cat = metrics["service_pressure"].get("pressure_category")

        # Compute strictly normalized 0–100 factor values
        factors: Dict[str, float] = {
            "gap_severity": self.normalize_gap_severity(metrics.get("gap_score")),
            "population_affected": self.normalize_population_affected(
                candidate.population, ref_population=cfg.reference_population
            ),
            "travel_time_need": self.normalize_travel_time_need(metrics.get("travel_time_score")),
            "capacity_pressure": self.normalize_capacity_pressure(
                metrics.get("capacity_score"), pressure_category=pressure_cat
            ),
            "equity_need": self.normalize_equity_need(metrics.get("equity_score")),
            "connectivity": self.normalize_connectivity(metrics.get("transport_connectivity_score")),
            "data_confidence": self.normalize_data_confidence(metrics.get("confidence_score")),
        }

        # Weighted combination
        raw_score = (
            (cfg.gap_weight * factors["gap_severity"])
            + (cfg.population_weight * factors["population_affected"])
            + (cfg.travel_need_weight * factors["travel_time_need"])
            + (cfg.capacity_pressure_weight * factors["capacity_pressure"])
            + (cfg.equity_need_weight * factors["equity_need"])
            + (cfg.connectivity_weight * factors["connectivity"])
            + (cfg.confidence_weight * factors["data_confidence"])
        )

        final_score = round(max(0.0, min(100.0, raw_score)), 1)
        conf_float = round(factors["data_confidence"] / 100.0, 2)

        reasons = self.generate_explanations(
            service_type=candidate.service_type,
            factors=factors,
            population=candidate.population,
            area_name=candidate.area_name,
        )

        weights_dict = {
            "gap_weight": cfg.gap_weight,
            "population_weight": cfg.population_weight,
            "travel_need_weight": cfg.travel_need_weight,
            "capacity_pressure_weight": cfg.capacity_pressure_weight,
            "equity_need_weight": cfg.equity_need_weight,
            "connectivity_weight": cfg.connectivity_weight,
            "confidence_weight": cfg.confidence_weight,
        }

        return ScoredCandidate(
            candidate=candidate,
            recommendation_score=final_score,
            rank=0,  # Rank will be assigned during batch sorting
            factor_values=factors,
            factor_weights=weights_dict,
            reasons=reasons,
            confidence=conf_float,
        )

    # --- 5. Batch Ranking & Deterministic Tie-Breaking ---
    def rank_candidates(
        self,
        db: Session,
        service_type: str,
        area_id: Optional[int] = None,
        min_gap_threshold: float = 20.0,
        config: Optional[RecommendationConfig] = None,
    ) -> Dict[str, Any]:
        """
        Generates candidates, excludes invalid candidates, scores valid candidates,
        and sorts them deterministically with stable secondary tie-breakers.
        """
        norm_type = self.validate_service_type(service_type)
        cfg = config or self.config

        # 1. Generate all candidates (including rejected to report exclusions)
        all_candidates = self.candidates.generate_candidates_for_service(
            db=db,
            service_type=norm_type,
            min_gap_threshold=min_gap_threshold,
            include_rejected=True,
        )

        # Filter by area_id if specified
        if area_id is not None:
            all_candidates = [c for c in all_candidates if c.area_id == area_id]

        # 2. Partition into valid and invalid
        valid_candidates: List[CandidateLocation] = []
        excluded_candidates: List[Dict[str, Any]] = []

        for c in all_candidates:
            if c.validity_status == "valid":
                valid_candidates.append(c)
            else:
                excluded_candidates.append({
                    "candidate_id": c.candidate_id,
                    "service_type": c.service_type,
                    "area_id": c.area_id,
                    "area_name": c.area_name,
                    "validity_status": c.validity_status,
                    "rejection_reason": c.rejection_reason or "Geospatial validity check failed",
                })

        # 3. Cache area analytics metrics to avoid redundant queries
        area_cache: Dict[int, Dict[str, Any]] = {}
        category = db.query(ServiceCategory).filter_by(code=norm_type).first()

        scored_list: List[ScoredCandidate] = []
        for cand in valid_candidates:
            if cand.area_id not in area_cache and category:
                area_obj = db.query(GeographicArea).filter_by(id=cand.area_id).first()
                if area_obj:
                    area_cache[cand.area_id] = self.analytics.analyze_area_category(
                        db, area_obj, category
                    )
                else:
                    area_cache[cand.area_id] = {}

            metrics = area_cache.get(cand.area_id, {})
            scored = self.score_candidate(cand, metrics, config=cfg)
            scored_list.append(scored)

        # 4. Deterministic Ranking & Tie-Breaking:
        # Sort primary: recommendation_score descending
        # Sort secondary (tie-breaker 1): population descending
        # Sort tertiary (tie-breaker 2): candidate_id ascending
        scored_list.sort(
            key=lambda item: (-item.recommendation_score, -item.population, item.candidate_id)
        )

        # Assign sequential rank (1, 2, 3...)
        for idx, item in enumerate(scored_list, start=1):
            item.rank = idx

        weights_used = {
            "gap_weight": cfg.gap_weight,
            "population_weight": cfg.population_weight,
            "travel_need_weight": cfg.travel_need_weight,
            "capacity_pressure_weight": cfg.capacity_pressure_weight,
            "equity_need_weight": cfg.equity_need_weight,
            "connectivity_weight": cfg.connectivity_weight,
            "confidence_weight": cfg.confidence_weight,
        }

        return {
            "service_type": norm_type,
            "total_candidates_evaluated": len(all_candidates),
            "valid_candidates_scored": len(scored_list),
            "excluded_candidates_count": len(excluded_candidates),
            "weights_used": weights_used,
            "ranked_candidates": scored_list,
            "excluded_candidates": excluded_candidates,
        }


# Singleton instance
default_recommendation_service = RecommendationScoringService()
