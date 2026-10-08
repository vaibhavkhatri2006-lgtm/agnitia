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
]
