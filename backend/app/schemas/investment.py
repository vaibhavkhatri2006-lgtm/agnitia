"""
Pydantic Schemas for Investment Priority Engine (Stage 4D Task 1).
Defines contracts for ranking candidate interventions by strategic investment return.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class InvestmentPriorityRequest(BaseModel):
    """Input parameters for evaluating investment priorities."""
    service_type: Optional[str] = Field(
        None,
        description="Filter by specific service type (healthcare, education, transport, water, market), or null for cross-sector",
        json_schema_extra={"example": "healthcare"},
    )
    min_gap_threshold: Optional[float] = Field(
        20.0,
        ge=0.0,
        le=100.0,
        description="Minimum gap score for candidate inclusion",
        json_schema_extra={"example": 20.0},
    )
    max_results: Optional[int] = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of ranked investment priorities to return",
        json_schema_extra={"example": 10},
    )


class RankedInvestmentItem(BaseModel):
    """A scored and ranked civic intervention investment opportunity."""
    rank: int = Field(..., description="Deterministic investment priority rank (1 = Highest)")
    candidate_id: str = Field(..., description="Candidate location identifier")
    service_type: str = Field(..., description="Civic service category")
    area_id: int = Field(..., description="Target geographic area ID")
    area_name: str = Field(..., description="Target geographic area name")
    latitude: float = Field(..., description="Candidate latitude")
    longitude: float = Field(..., description="Candidate longitude")
    investment_priority_score: float = Field(..., description="Normalized composite investment score (0-100)")
    priority_tier: str = Field(..., description="Strategic tier: Highest Priority, High Priority, Moderate Priority, Low Priority")
    recommendation_score: float = Field(..., description="Stage 4B recommendation priority score (0-100)")
    expected_impact_score: float = Field(..., description="Estimated accessibility and coverage impact score (0-100)")
    population_affected: int = Field(..., description="Beneficiary population in target area")
    gap_severity: float = Field(..., description="Baseline service gap severity (0-100)")
    equity_need: float = Field(..., description="Demographic and socioeconomic vulnerability factor (0-100)")
    estimated_cost_tier: str = Field(..., description="Estimated capital expenditure tier (Standard Local Facility)")
    rationale: str = Field(..., description="Human-readable justification for prioritizing this investment")
    primary_drivers: List[str] = Field(..., description="Key criteria driving this investment rank")


class InvestmentPriorityResponse(BaseModel):
    """Response containing deterministic ranked investment priorities."""
    service_type: Optional[str] = Field(None, description="Scope filter applied (or null if cross-sector)")
    total_interventions_evaluated: int = Field(..., description="Total candidate locations evaluated")
    ranked_investments: List[RankedInvestmentItem] = Field(..., description="Ordered list of priority investments")
