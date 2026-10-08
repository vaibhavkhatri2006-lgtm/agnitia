"""
Schemas for civic rankings and leaderboard representations in CivicPulse.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class UnderservedAreaRankingItem(BaseModel):
    """Represents a single ranked underserved geographic area."""
    rank: int = Field(..., description="1-based sequential priority rank")
    area_id: int = Field(..., description="Geographic area ID")
    area_name: str = Field(..., description="Geographic area name")
    area_type: str = Field(..., description="Area type (city, ward, neighbourhood)")
    population: int = Field(..., description="Total resident population")
    accessibility_score: float = Field(..., description="Accessibility score (0.0 to 100.0)")
    gap_score: float = Field(..., description="Deficit gap score (0.0 to 100.0)")
    desert_classification: str = Field(..., description="Classification category (e.g. Critical Desert, Underserved)")
    category_evaluated: str = Field(..., description="Specific category or 'composite' across all categories")
    most_critical_category: Optional[str] = Field(None, description="Category with highest gap for this area")
    nearest_service_name: Optional[str] = Field(None, description="Name of nearest facility if evaluated for single category")
    service_pressure_category: Optional[str] = Field(None, description="Service pressure tier (Critical, High, Moderate, Low)")
    confidence_score: float = Field(..., description="Telemetry and report confidence score (0.0 to 1.0)")


class UnderservedRankingsResponse(BaseModel):
    """Response containing ranked list of underserved civic areas."""
    category_evaluated: str = Field(..., description="Category filter evaluated ('composite' or specific category code)")
    total_areas_evaluated: int = Field(..., description="Number of geographic areas scanned")
    underserved_areas_count: int = Field(..., description="Number of areas classified as Underserved or Critical Desert")
    rankings: List[UnderservedAreaRankingItem] = Field(default_factory=list, description="Ranked areas sorted by severity")
