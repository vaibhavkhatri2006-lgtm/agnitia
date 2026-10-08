"""
Decision and recommendation support package.
Stage 4A: Candidate Location Engine.
"""
from app.decision.candidates import (
    CandidateLocation,
    CandidateLocationService,
    default_candidate_service,
)

__all__ = [
    "CandidateLocation",
    "CandidateLocationService",
    "default_candidate_service",
]
