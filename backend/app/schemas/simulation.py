"""
Pydantic Schemas for the What-If / Intervention Simulation Engine (Stage 4C).
Defines request and response data contracts for simulating new civic facility placement.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """Input payload for what-if intervention simulation."""
    service_type: str = Field(
        ...,
        description="Service type: healthcare, education, transport, water, market",
        json_schema_extra={"example": "healthcare"},
    )
    candidate_id: Optional[str] = Field(
        None,
        description="Candidate ID from Stage 4A/4B (e.g., 'cand-healthcare-9-centroid')",
        json_schema_extra={"example": "cand-healthcare-9-centroid"},
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Proposed facility latitude (-90 to 90)",
        json_schema_extra={"example": 12.984123},
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Proposed facility longitude (-180 to 180)",
        json_schema_extra={"example": 77.632145},
    )
    scope: Optional[str] = Field(
        "city",
        description="Analysis scope: 'city', 'neighbourhoods', or specific area ID",
        json_schema_extra={"example": "city"},
    )
    proposed_name: Optional[str] = Field(
        None,
        description="Optional descriptive name for the simulated facility",
        json_schema_extra={"example": "Highlands Valley Community Health Center"},
    )
    proposed_capacity: Optional[int] = Field(
        5000,
        ge=1,
        description="Proposed service capacity units (e.g. population served / patient capacity)",
        json_schema_extra={"example": 5000},
    )


class SimulationStateMetrics(BaseModel):
    """Metrics representing the state of service provision before or after intervention."""
    accessibility_score: float = Field(..., description="Population-weighted accessibility score (0-100)")
    gap_score: float = Field(..., description="Service gap score (100 - accessibility_score, 0-100)")
    service_coverage: float = Field(..., description="Service coverage percentage (0-100%)")
    underserved_population: int = Field(..., description="Population living in underserved or desert areas")
    average_travel_time_minutes: float = Field(..., description="Average estimated travel time to nearest service (minutes)")


class SimulationImpactMetrics(BaseModel):
    """Measurable change and impact resulting from the simulated intervention."""
    accessibility_improvement: float = Field(..., description="Accessibility score gain (+ points)")
    gap_reduction: float = Field(..., description="Gap score reduction (- points)")
    coverage_improvement: float = Field(..., description="Service coverage expansion (+ percentage points)")
    underserved_population_reduction: int = Field(..., description="Reduction in underserved population (residents)")
    population_gaining_access: int = Field(..., description="Population newly gaining meaningful access")
    travel_time_improvement_minutes: float = Field(..., description="Travel time saved (minutes)")


class TargetAreaImpact(BaseModel):
    """Detailed before-and-after evaluation for the specific receiving geographic area."""
    area_id: int = Field(..., description="ID of receiving geographic area")
    area_name: str = Field(..., description="Name of receiving geographic area")
    area_type: str = Field(..., description="Geographic administrative level (e.g. neighbourhood)")
    population: int = Field(..., description="Population of receiving geographic area")
    before_accessibility: float = Field(..., description="Accessibility score before intervention")
    after_accessibility: float = Field(..., description="Accessibility score after intervention")
    accessibility_improvement: float = Field(..., description="Accessibility improvement in target area")
    before_gap: float = Field(..., description="Gap score before intervention")
    after_gap: float = Field(..., description="Gap score after intervention")
    before_classification: str = Field(..., description="Service desert classification before intervention")
    after_classification: str = Field(..., description="Service desert classification after intervention")
    before_travel_time_minutes: Optional[float] = Field(None, description="Travel time to nearest service before")
    after_travel_time_minutes: Optional[float] = Field(None, description="Travel time to simulated service after")
    travel_time_saved_minutes: Optional[float] = Field(None, description="Travel time saved in target area")


class SimulationResponse(BaseModel):
    """Complete simulation result comparing before vs after state and measurable impact."""
    simulation_id: str = Field(..., description="Unique simulation run identifier")
    service_type: str = Field(..., description="Evaluated service category")
    candidate_id: Optional[str] = Field(None, description="Associated candidate ID if provided")
    latitude: float = Field(..., description="Simulated facility latitude")
    longitude: float = Field(..., description="Simulated facility longitude")
    scope: str = Field(..., description="Evaluated analysis scope")
    target_area: TargetAreaImpact = Field(..., description="Impact breakdown for target locality")
    before: SimulationStateMetrics = Field(..., description="Baseline metrics before intervention")
    after: SimulationStateMetrics = Field(..., description="Recalculated metrics after intervention")
    impact: SimulationImpactMetrics = Field(..., description="Measurable impact delta")
    explanation: str = Field(..., description="Natural language justification of intervention impact")
    primary_factors: List[str] = Field(..., description="Key drivers responsible for the improvement")
    confidence: float = Field(..., description="Data confidence score (0.0 to 1.0)")
