"""
Pydantic schemas for the Planner Command Center (Stage 8).
Supports Underserved Rankings, Service Comparisons, Capacity Pressure,
Equity Diagnostics, Reality Gap verification, and Ranked Recommendations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PlannerUnderservedAreaItem(BaseModel):
    """Ranked underserved civic area for planner command center."""
    rank: int = Field(..., description="Deterministic priority rank (1 = most underserved)")
    area: str = Field(..., description="Geographic area name")
    area_id: int = Field(..., description="Geographic area database ID")
    area_type: str = Field(..., description="Area scale: neighbourhood, ward, district, city")
    accessibility: float = Field(..., description="Composite accessibility score (0 to 100)")
    gap: float = Field(..., description="Composite gap score (0 to 100)")
    population: int = Field(..., description="Local population")
    main_service_gap: str = Field(..., description="Category code with highest unmet gap")
    priority: str = Field(..., description="Priority classification: Critical, High, Medium, Low")


class PlannerUnderservedRankingsResponse(BaseModel):
    """Leaderboard of underserved localities for planner dashboard."""
    total_areas_evaluated: int
    underserved_count: int
    rankings: List[PlannerUnderservedAreaItem]


class PlannerServiceComparisonItem(BaseModel):
    """Service-wise comparative metric for a single civic domain."""
    service_type: str = Field(..., description="Category code: healthcare, education, transport, water, market")
    service_name: str = Field(..., description="Human-readable category name")
    accessibility_score: float = Field(..., description="Average or area-specific accessibility score (0 to 100)")
    gap_score: float = Field(..., description="Gap score (0 to 100)")
    status: str = Field(..., description="Desert classification or availability tier")
    distance_km: Optional[float] = Field(None, description="Average or direct distance to nearest facility in km")
    travel_time_min: Optional[float] = Field(None, description="Estimated travel time in minutes")
    capacity_status: str = Field(..., description="Capacity load category: Normal, Moderate, Critical, Low")
    rank: int = Field(..., description="Relative standing (1 = highest urgency/gap)")


class PlannerServiceComparisonResponse(BaseModel):
    """Comparative breakdown across the 5 core civic service sectors."""
    area_id: Optional[int] = Field(None, description="Specific area ID if filtered, or None for city-wide")
    area_name: Optional[str] = Field(None, description="Specific area name if filtered, or 'City-wide Average'")
    services: List[PlannerServiceComparisonItem]


class PlannerCapacityPressureItem(BaseModel):
    """Facility or area capacity pressure breakdown item."""
    area_id: Optional[int] = None
    area_name: Optional[str] = None
    service_type: str
    demand: float = Field(..., description="Population demand load")
    capacity: float = Field(..., description="Total nominal facility capacity")
    pressure: float = Field(..., description="Pressure index / ratio (e.g. demand / capacity)")
    status: str = Field(..., description="Status tier: Low, Moderate, High, Critical")
    utilization_pct: float = Field(..., description="Capacity utilization percentage")


class PlannerCapacityPressureResponse(BaseModel):
    """Aggregate capacity pressure evaluation for planner command center."""
    service_type: Optional[str] = Field(None, description="Filter category code or None for composite")
    area_id: Optional[int] = Field(None, description="Filter area ID or None for city-wide")
    demand: float = Field(..., description="Total evaluated demand population")
    capacity: float = Field(..., description="Total available facility capacity")
    pressure: float = Field(..., description="Aggregate demand-to-capacity pressure ratio")
    status: str = Field(..., description="Overall pressure status: Low, Moderate, High, Critical")
    items: List[PlannerCapacityPressureItem] = Field(default_factory=list)


class PlannerEquityRealityGapResponse(BaseModel):
    """Combined equity diagnostics and ground-truth reality gap metrics."""
    area_id: int
    area_name: str
    category_code: Optional[str] = None
    equity_score: float = Field(..., description="Demographic equity score (0 to 100)")
    main_contributing_factors: List[str] = Field(..., description="Primary explanatory factors driving equity score")
    map_access_score: float = Field(..., description="Nominal GIS map accessibility score (0 to 100)")
    real_world_score: float = Field(..., description="Real-world accessibility score adjusted for citizen-reported outages")
    reality_gap: float = Field(..., description="Discrepancy points between map access and ground reality")
    confidence: float = Field(..., description="Data confidence score (0.0 to 1.0)")
    active_reports_count: int = Field(0, description="Number of active citizen/community reports in catchment")
    divergence_level: str = Field("None", description="Reality gap divergence severity: None, Minor, Moderate, Severe")


class PlannerCandidateInfo(BaseModel):
    """Spatial and demographic summary of a recommended candidate site."""
    candidate_id: str
    service_type: str
    latitude: float
    longitude: float
    area_id: int
    area_name: str
    population: int
    strategy: str


class PlannerExpectedImpact(BaseModel):
    """Estimated intervention impact on civic service accessibility."""
    accessibility_improvement: float = Field(..., description="Direct accessibility score point increase in target area")
    coverage_gain: float = Field(..., description="City-wide population coverage gain percentage")
    impact_score: float = Field(..., description="Deterministic impact score (0 to 100)")
    summary: str = Field(..., description="Human-readable impact statement")


class PlannerRecommendationItem(BaseModel):
    """Fully explainable intervention recommendation item."""
    recommended_candidate: PlannerCandidateInfo
    score: float = Field(..., description="Multi-factor recommendation priority score (0 to 100)")
    rank: int = Field(..., description="Priority rank (1 = best recommended)")
    reasons: List[str] = Field(..., description="Explainable driving factors for this recommendation")
    expected_impact: PlannerExpectedImpact
    confidence: float = Field(..., description="Data confidence score (0.0 to 1.0)")


class PlannerRecommendationsResponse(BaseModel):
    """Top recommended intervention candidates for the planner dashboard."""
    service_type: str
    area_id: Optional[int] = None
    total_candidates_evaluated: int
    recommended_candidate: Optional[PlannerCandidateInfo] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    reasons: Optional[List[str]] = None
    expected_impact: Optional[PlannerExpectedImpact] = None
    confidence: Optional[float] = None
    candidates: List[PlannerRecommendationItem] = Field(default_factory=list)


class PlannerOverviewResponse(BaseModel):
    """Unified planner command center dashboard payload."""
    total_areas_monitored: int
    most_underserved_areas: List[PlannerUnderservedAreaItem]
    service_comparison: List[PlannerServiceComparisonItem]
    capacity_pressure: PlannerCapacityPressureResponse
    top_recommendation: Optional[PlannerRecommendationItem] = None
