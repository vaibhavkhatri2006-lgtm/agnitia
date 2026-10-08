"""
Pydantic Schemas for Future-Risk Foundation Engine (Stage 4D Task 3).
Defines contracts for projecting demand growth and evaluating emerging civic risk.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class FutureRiskRequest(BaseModel):
    """Input parameters for future civic risk estimation."""
    growth_rate_pct: Optional[float] = Field(
        15.0,
        ge=0.0,
        le=100.0,
        description="Projected demand/population growth percentage",
        json_schema_extra={"example": 15.0},
    )
    time_horizon_years: Optional[int] = Field(
        5,
        ge=1,
        le=30,
        description="Projection horizon in years (1 to 30)",
        json_schema_extra={"example": 5},
    )
    service_type: Optional[str] = Field(
        None,
        description="Filter to specific service type (healthcare, education, transport, water, market), or null for cross-sector",
        json_schema_extra={"example": "healthcare"},
    )
    area_id: Optional[int] = Field(
        None,
        description="Filter to specific geographic area ID, or null for all localities",
        json_schema_extra={"example": 9},
    )


class AreaFutureRiskItem(BaseModel):
    """Locality-level future risk evaluation under demand growth."""
    area_id: int = Field(..., description="Geographic area ID")
    area_name: str = Field(..., description="Geographic area name")
    current_population: int = Field(..., description="Current baseline population")
    projected_population: int = Field(..., description="Projected future demand population")
    current_risk_score: float = Field(..., description="Baseline risk score (0-100)")
    projected_risk_score: float = Field(..., description="Projected risk score under demand growth (0-100)")
    risk_increase: float = Field(..., description="Risk score escalation (+ points)")
    current_risk_category: str = Field(..., description="Baseline risk level: Low, Moderate, High, Critical")
    projected_risk_category: str = Field(..., description="Projected risk level: Low, Moderate, High, Critical")
    capacity_status: str = Field(..., description="Current capacity load pressure")
    primary_vulnerability: str = Field(..., description="Primary risk driver")


class FutureRiskResponse(BaseModel):
    """Summary future civic risk estimate under projected growth."""
    service_type: Optional[str] = Field(None, description="Evaluated service category")
    growth_rate_pct: float = Field(..., description="Simulated demand growth rate percentage")
    time_horizon_years: int = Field(..., description="Projection horizon in years")
    evaluated_areas_count: int = Field(..., description="Count of evaluated geographic areas")
    current_risk_score: float = Field(..., description="Average current civic risk score (0-100)")
    projected_risk_score: float = Field(..., description="Average projected civic risk score (0-100)")
    risk_increase: float = Field(..., description="Net risk escalation (+ points)")
    current_risk_category: str = Field(..., description="Systemic baseline risk tier")
    projected_risk_category: str = Field(..., description="Systemic projected risk tier")
    risk_trend: str = Field(..., description="Growth trend classification (Accelerating Deficit, Growing Pressure, Stable)")
    areas_at_risk: List[AreaFutureRiskItem] = Field(..., description="Area-level risk breakdown")
    vulnerability_factors: List[str] = Field(..., description="Key drivers responsible for projected risk")
    is_demo_estimate: bool = Field(True, description="Explicit flag indicating simplified deterministic demo projection")
    label: str = Field("Demo Estimate - Deterministic Future Risk Foundation", description="Official display badge")
    disclaimer: str = Field(..., description="Methodological planning disclaimer")
