"""
Schemas for civic infrastructure, localities (geographic areas), and services.
Provides frontend-safe data transfer objects for UI maps, dropdowns, and scorecards.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ServiceCategoryItem(BaseModel):
    """Represents a supported civic service category."""
    id: int = Field(..., description="Unique category ID")
    code: str = Field(..., description="Short category code (e.g. healthcare, education)")
    name: str = Field(..., description="Display name for the category")
    description: Optional[str] = Field(None, description="Detailed category description")
    icon: Optional[str] = Field(None, description="Icon identifier for frontend rendering")
    is_active: bool = Field(True, description="Whether category is active")

    model_config = {"from_attributes": True}


class ServiceItem(BaseModel):
    """Represents an active or cataloged civic service facility."""
    id: int = Field(..., description="Unique service ID")
    name: str = Field(..., description="Facility name (e.g. Central Metro Hospital)")
    category_id: int = Field(..., description="Category foreign key ID")
    category_code: str = Field(..., description="Category code (e.g. healthcare)")
    category_name: str = Field(..., description="Category display name")
    area_id: Optional[int] = Field(None, description="Host geographic area ID")
    area_name: Optional[str] = Field(None, description="Host geographic area name")
    latitude: float = Field(..., description="WGS84 latitude coordinate")
    longitude: float = Field(..., description="WGS84 longitude coordinate")
    status: str = Field(..., description="Operational status: operational, degraded, temporarily_unavailable, closed")
    source_type: str = Field(..., description="Origin data source: simulated_demo, government, community, etc.")
    verification_status: str = Field(..., description="Verification status: verified, unverified, pending")
    confidence_score: float = Field(..., description="Data confidence score (0.0 - 1.0)")
    capacity: Optional[int] = Field(None, description="Designed service capacity")
    current_load: Optional[int] = Field(None, description="Current estimated utilization load")
    operating_hours: Optional[str] = Field(None, description="Operating hours text if available")

    model_config = {"from_attributes": True}


class GeographicAreaItem(BaseModel):
    """Represents a geographic administrative boundary or neighbourhood locality."""
    id: int = Field(..., description="Unique geographic area ID")
    name: str = Field(..., description="Administrative name (e.g. Highlands Valley)")
    area_type: str = Field(..., description="Boundary type: city, ward, neighbourhood")
    parent_id: Optional[int] = Field(None, description="Parent administrative area ID")
    population: int = Field(..., description="Total estimated resident population")

    model_config = {"from_attributes": True}
