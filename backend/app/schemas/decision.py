"""
Pydantic schemas for Candidate Location Engine (Stage 4A).
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CandidateLocationResponse(BaseModel):
    candidate_id: str = Field(..., description="Unique deterministic candidate identifier")
    service_type: str = Field(..., description="Target service category code (e.g. healthcare, water)")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    area_id: int = Field(..., description="Assigned geographic area ID")
    area_name: str = Field(..., description="Name of assigned geographic area")
    source_reason: str = Field(..., description="Analytical justification for candidate placement")
    current_accessibility: float = Field(..., description="Current accessibility score of the area")
    population: int = Field(..., description="Population residing in the analysis area")
    current_gap: float = Field(..., description="Current service gap score (100 - accessibility)")
    nearby_service_count: int = Field(..., description="Count of existing services within catchment range")
    validity_status: str = Field(..., description="Validation status: 'valid', 'rejected', etc.")
    strategy: str = Field(..., description="Strategy used: 'centroid', 'population_node', 'gap_perimeter'")
    rejection_reason: Optional[str] = Field(None, description="Explanation if candidate was rejected")


class CandidateGenerationRequest(BaseModel):
    service_type: str = Field(..., description="Civic service type (healthcare, education, transport, water, market)")
    min_gap_threshold: float = Field(20.0, ge=0.0, le=100.0, description="Minimum gap score for an area to qualify")
    max_accessibility: float = Field(80.0, ge=0.0, le=100.0, description="Maximum accessibility score (excludes well-served areas)")
    include_rejected: bool = Field(False, description="Whether to include rejected candidate points in output")


class CandidateGenerationResponse(BaseModel):
    service_type: str
    total_candidates: int
    valid_candidates_count: int
    rejected_candidates_count: int
    candidates: List[CandidateLocationResponse]
