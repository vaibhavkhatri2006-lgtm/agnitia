"""
Decision and recommendation support package.
Stage 4A: Candidate Location Engine.
"""
from app.decision.candidates import (
    CandidateLocation,
    CandidateLocationService,
    default_candidate_service,
)
from app.decision.recommendation import (
    RecommendationConfig,
    ScoredCandidate,
    RecommendationScoringService,
    default_recommendation_service,
)

from app.decision.simulation import (
    InterventionSimulationService,
    default_simulation_service,
)

from app.decision.investment import (
    InvestmentPriorityService,
    default_investment_service,
)
from app.decision.resilience import (
    ResilienceFailureService,
    default_resilience_service,
)
from app.decision.future_risk import (
    FutureRiskService,
    default_future_risk_service,
)

__all__ = [
    "CandidateLocation",
    "CandidateLocationService",
    "default_candidate_service",
    "RecommendationConfig",
    "ScoredCandidate",
    "RecommendationScoringService",
    "default_recommendation_service",
    "InterventionSimulationService",
    "default_simulation_service",
    "InvestmentPriorityService",
    "default_investment_service",
    "ResilienceFailureService",
    "default_resilience_service",
    "FutureRiskService",
    "default_future_risk_service",
]

