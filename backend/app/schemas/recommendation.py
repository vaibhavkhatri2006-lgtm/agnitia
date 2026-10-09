"""
Pydantic schemas for Recommendation Scoring Engine (Stage 4B).
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FactorValues(BaseModel):
    gap_severity: float = Field(..., description="Normalized gap severity score (0-100)")
    population_affected: float = Field(..., description="Normalized population affected score (0-100)")
    travel_time_need: float = Field(..., description="Normalized travel time deficit (0-100)")
    capacity_pressure: float = Field(..., description="Normalized service load and capacity pressure (0-100)")
    equity_need: float = Field(..., description="Normalized demographic and equity need (0-100)")
    connectivity: float = Field(..., description="Normalized transport connectivity (0-100)")
    data_confidence: float = Field(..., description="Normalized data confidence (0-100)")


class FactorWeights(BaseModel):
    gap_weight: float = Field(0.30, description="Weight for gap severity (30%)")
    population_weight: float = Field(0.25, description="Weight for population affected (25%)")
    travel_need_weight: float = Field(0.15, description="Weight for travel-time need (15%)")
    capacity_pressure_weight: float = Field(0.10, description="Weight for capacity pressure (10%)")
    equity_need_weight: float = Field(0.10, description="Weight for equity need (10%)")
    connectivity_weight: float = Field(0.05, description="Weight for transport connectivity (5%)")
    confidence_weight: float = Field(0.05, description="Weight for data confidence (5%)")


class ScoredCandidateResponse(BaseModel):
    candidate_id: str
    service_type: str
    rank: int
    recommendation_score: float = Field(..., description="Composite recommendation priority score (0-100)")
    latitude: float
    longitude: float
    area_id: int
    area_name: str
    population: int
    strategy: str
    confidence: float
    expected_gain_pts: Optional[float] = Field(None, description="Expected access-score gain (points)")
    factor_values: FactorValues
    factor_weights: FactorWeights
    reasons: List[str]


class ExcludedCandidateResponse(BaseModel):
    candidate_id: str
    service_type: str
    area_id: int
    area_name: str
    validity_status: str
    rejection_reason: Optional[str] = None


class RecommendationRequest(BaseModel):
    service_type: str = Field(..., description="Civic service type (healthcare, education, transport, water, market)")
    area_id: Optional[int] = Field(None, description="Optional area ID filter")
    min_gap_threshold: float = Field(20.0, ge=0.0, le=100.0, description="Minimum gap score threshold")
    weights: Optional[Dict[str, float]] = Field(None, description="Optional custom weights dictionary")


class RecommendationResponse(BaseModel):
    service_type: str
    total_candidates_evaluated: int
    valid_candidates_scored: int
    excluded_candidates_count: int
    weights_used: FactorWeights
    ranked_candidates: List[ScoredCandidateResponse]
    excluded_candidates: List[ExcludedCandidateResponse]
