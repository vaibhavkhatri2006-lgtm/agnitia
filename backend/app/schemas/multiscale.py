"""
Pydantic schemas for Multi-Scale Geographic Analysis (Stage 10).
Defines contracts for hierarchy trees, relationship validation, scope availability,
and multi-scale metrics aggregation.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GeographicHierarchyNode(BaseModel):
    """Recursive node representing a geographic area within administrative hierarchy."""
    id: int = Field(..., description="Geographic area ID")
    name: str = Field(..., description="Locality or administrative area name")
    area_type: str = Field(..., description="Administrative scale: local, neighbourhood, ward, district, city, region, country, global")
    population: int = Field(..., description="Resident population")
    parent_id: Optional[int] = Field(None, description="Parent administrative area ID")
    children: List["GeographicHierarchyNode"] = Field(default_factory=list, description="Sub-areas contained within this area")


class HierarchyValidationReport(BaseModel):
    """Audit report validating geographic hierarchy integrity."""
    status: str = Field(..., description="'valid' or 'invalid'")
    is_valid: bool = Field(..., description="True if no hierarchy integrity violations found")
    total_areas: int = Field(..., description="Total geographic areas scanned")
    root_areas_count: int = Field(..., description="Number of root areas without parents")
    max_depth: int = Field(..., description="Maximum depth of the geographic hierarchy tree")
    levels_found: List[str] = Field(..., description="Administrative levels represented in database")
    valid_relationships_count: int = Field(..., description="Count of valid parent-child linkages")
    orphan_count: int = Field(..., description="Count of invalid or orphaned references")
    circular_references_count: int = Field(..., description="Count of detected circular loops")
    errors: List[str] = Field(default_factory=list, description="List of detected errors if any")


class HierarchyRelationshipValidationRequest(BaseModel):
    """Input payload to test validity of a parent-child relationship."""
    parent_id: Optional[int] = Field(None, description="Parent area ID")
    child_id: Optional[int] = Field(None, description="Child area ID")
    parent_type: Optional[str] = Field(None, description="Parent administrative scale")
    child_type: Optional[str] = Field(None, description="Child administrative scale")


class HierarchyRelationshipValidationResponse(BaseModel):
    """Result of relationship validation check."""
    is_valid: bool = Field(..., description="Whether relationship satisfies hierarchy rules")
    reason: str = Field(..., description="Explanation of validation determination")
    parent_type: Optional[str] = Field(None, description="Parent area type")
    child_type: Optional[str] = Field(None, description="Child area type")


class ScopeAvailabilityItem(BaseModel):
    """Data availability summary for a specific geographic scale."""
    scope: str = Field(..., description="Canonical scale name: local, neighbourhood, ward, city, region, country, global")
    display_name: str = Field(..., description="User-friendly scale label")
    available: bool = Field(..., description="Whether dataset contains active records at this scale")
    area_count: int = Field(..., description="Number of available geographic units at this scale")
    description: str = Field(..., description="Scale explanation and coverage status")


class MultiScaleScopesResponse(BaseModel):
    """List of all recognized geographic scopes and their dataset availability."""
    supported_scopes: List[str] = Field(..., description="Scopes with available data")
    unavailable_scopes: List[str] = Field(..., description="Recognized scopes without data in current dataset")
    scopes: List[ScopeAvailabilityItem] = Field(..., description="Full availability details per scale")


class MultiScaleAreaSummary(BaseModel):
    """Per-area aggregated metric within a multi-scale analysis query."""
    area_id: int
    name: str
    area_type: str
    population: int
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    accessibility_score: float
    gap_score: float
    desert_classification: str
    child_count: int = 0


class MultiScaleAnalyticsResponse(BaseModel):
    """Consolidated response for scope-aware analytics queries."""
    scope: str = Field(..., description="Requested geographic scale: local, neighbourhood, ward, city, region, country, global")
    available: bool = Field(..., description="True if data is available for this scope")
    status: str = Field(..., description="'success' or 'no_data'")
    message: Optional[str] = Field(None, description="Informational message or missing data notice")
    total_areas: int = Field(0, description="Count of evaluated areas at this scale")
    total_population: int = Field(0, description="Total population represented at this scale")
    average_accessibility: Optional[float] = Field(None, description="Population-weighted average accessibility score")
    average_gap: Optional[float] = Field(None, description="Population-weighted average gap score")
    coverage_pct: Optional[float] = Field(None, description="Percentage of population living in served areas")
    areas: List[MultiScaleAreaSummary] = Field(default_factory=list, description="Area-level metrics for this scale")
    is_demo_data: bool = Field(True, description="Identifies data as simulated demo records")
    label: str = Field("Multi-Scale Geographic Analysis", description="UI categorization label")
