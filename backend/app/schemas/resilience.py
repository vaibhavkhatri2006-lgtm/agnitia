"""
Pydantic Schemas for Failure / Resilience Simulation Engine (Stage 4D Task 2).
Defines contracts for evaluating the impact and systemic resilience of civic facility failures.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class FailureSimulationRequest(BaseModel):
    """Input payload to simulate the failure/unavailability of a specific service."""
    service_id: int = Field(
        ...,
        description="ID of the civic facility to simulate outage/failure for",
        json_schema_extra={"example": 1},
    )
    scope: Optional[str] = Field(
        "city",
        description="Analysis scope: 'city', 'neighbourhoods', or specific area ID",
        json_schema_extra={"example": "city"},
    )


class AffectedAreaFailureItem(BaseModel):
    """Detailed failure impact on a specific geographic locality."""
    area_id: int = Field(..., description="Area ID")
    area_name: str = Field(..., description="Area name")
    population: int = Field(..., description="Area population")
    before_accessibility: float = Field(..., description="Accessibility score before failure")
    after_accessibility: float = Field(..., description="Accessibility score during simulated outage")
    accessibility_drop: float = Field(..., description="Loss in accessibility score points")
    before_classification: str = Field(..., description="Service desert status before failure")
    after_classification: str = Field(..., description="Service desert status during failure")
    was_nearest_service: bool = Field(..., description="Whether this facility was the area's primary nearest facility")
    became_underserved: bool = Field(..., description="Whether the area dropped below coverage threshold into underserved status")


class FailureSimulationResponse(BaseModel):
    """Result of facility failure simulation measuring systemic resilience."""
    service_id: int = Field(..., description="Target service identifier")
    service_name: str = Field(..., description="Name of the failed facility")
    category_code: str = Field(..., description="Service category code (e.g. healthcare)")
    category_name: str = Field(..., description="Service category display name")
    location_area_name: str = Field(..., description="Locality where the facility resides")
    scope: str = Field(..., description="Evaluation scope")
    baseline_accessibility: float = Field(..., description="Baseline average accessibility before failure (0-100)")
    failure_accessibility: float = Field(..., description="Average accessibility during failure (0-100)")
    accessibility_drop: float = Field(..., description="Loss in accessibility (- points)")
    baseline_coverage: float = Field(..., description="Baseline service coverage percentage (0-100%)")
    failure_coverage: float = Field(..., description="Service coverage percentage during failure (0-100%)")
    coverage_loss: float = Field(..., description="Service coverage loss (percentage points lost)")
    directly_affected_population: int = Field(..., description="Residents whose primary facility failed")
    newly_underserved_population: int = Field(..., description="Residents whose locality transitioned into underserved status")
    resilience_score: float = Field(..., description="Systemic resilience rating (0-100, 100 = completely resilient)")
    criticality_tier: str = Field(..., description="Criticality rating: Critical Infrastructure, High Dependency, Moderate Vulnerability, Resilient")
    single_point_of_failure: bool = Field(..., description="Whether this facility represents a single point of failure")
    explanation: str = Field(..., description="Natural language civic explanation of the failure impact")
    affected_areas: List[AffectedAreaFailureItem] = Field(..., description="Locality-by-locality impact breakdown")
