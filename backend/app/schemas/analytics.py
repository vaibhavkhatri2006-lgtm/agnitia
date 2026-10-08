"""
Pydantic schemas for Geospatial and Analytics Engine endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ServicePressureResponse(BaseModel):
    capacity_score: float = Field(..., description="Normalized capacity score (0-100)")
    pressure_ratio: float = Field(..., description="Demand to available capacity ratio")
    pressure_category: str = Field(..., description="Categorical service pressure (Low, Moderate, High, Critical)")
    pressure_score: float = Field(..., description="Continuous pressure score (0-100)")
    capacity: Optional[int] = Field(None, description="Reported capacity value")
    current_load: Optional[int] = Field(None, description="Reported load or demand value")
    data_quality: str = Field(..., description="Data quality indicator flag")


class CategoryAnalyticsResponse(BaseModel):
    area_id: int
    area_name: str
    area_type: str
    category_id: int
    category_code: str
    category_name: str
    nearest_service_id: Optional[int] = None
    nearest_service_name: Optional[str] = None
    nearest_service_status: Optional[str] = None
    distance_km: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    travel_time_score: float
    availability_score: float
    capacity_score: float
    transport_connectivity_score: float
    equity_score: float
    accessibility_score: float
    gap_score: float
    service_desert_classification: str
    service_pressure: ServicePressureResponse
    confidence_score: float
    reality_gap_score: float
    reality_gap_level: str
    reality_gap_summary: str


class AreaSummaryAnalyticsResponse(BaseModel):
    area_id: int
    area_name: str
    area_type: str
    population: int
    composite_accessibility_score: float
    composite_gap_score: float
    composite_desert_classification: str
    categories_evaluated: int
    category_breakdown: Optional[List[CategoryAnalyticsResponse]] = None


class ServiceDesertItemResponse(BaseModel):
    area_id: int
    area_name: str
    category_code: str
    category_name: str
    accessibility_score: float
    gap_score: float
    service_desert_classification: str
    nearest_service_name: Optional[str] = None
    distance_km: Optional[float] = None
    pressure_category: str


class AnalyticsConfigResponse(BaseModel):
    travel_time_weight: float
    availability_weight: float
    capacity_weight: float
    transport_weight: float
    equity_weight: float
    travel_speeds_kmh: Dict[str, float]
    availability_scores: Dict[str, float]
    travel_time_thresholds: List[List[Any]]
    desert_classifications: List[List[Any]]
