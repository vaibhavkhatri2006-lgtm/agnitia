from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, model_validator


class AnalyticsConfig(BaseModel):
    """
    Central, validated configuration for the CivicPulse Geospatial & Analytics Engine.
    All weights, speed models, and desert classification thresholds are centralized here.
    """
    # 1. Configurable Weights for Accessibility Score (Must sum to 1.0)
    travel_time_weight: float = Field(0.30, ge=0.0, le=1.0, description="Weight for Travel Time Score (30%)")
    availability_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for Service Availability Score (20%)")
    capacity_weight: float = Field(0.20, ge=0.0, le=1.0, description="Weight for Capacity Score (20%)")
    transport_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for Transport Connectivity Score (15%)")
    equity_weight: float = Field(0.15, ge=0.0, le=1.0, description="Weight for Equity Score (15%)")

    # 2. Configurable Assumed Travel Speeds (km/h) for Deterministic Estimates
    walking_speed_kmh: float = Field(4.5, gt=0.0, description="Assumed walking speed (km/h)")
    transit_speed_kmh: float = Field(22.0, gt=0.0, description="Assumed public transit speed (km/h)")
    driving_speed_kmh: float = Field(35.0, gt=0.0, description="Assumed driving speed (km/h)")
    max_catchment_distance_km: float = Field(2.5, gt=0.0, description="Maximum catchment distance in km for service access")
    default_travel_mode: str = Field("transit", description="Assumed default mode for travel time estimation")

    @property
    def travel_speeds_kmh(self) -> Dict[str, float]:
        return {
            "walking": self.walking_speed_kmh,
            "transit": self.transit_speed_kmh,
            "driving": self.driving_speed_kmh,
        }

    # 3. Status to Availability Score Mapping (0-100)
    availability_scores: Dict[str, float] = Field(
        default_factory=lambda: {
            "operational": 100.0,
            "limited": 60.0,
            "degraded": 50.0,
            "temporarily_unavailable": 20.0,
            "closed": 0.0,
        }
    )

    # 4. Travel Time Score Thresholds: [(max_minutes, score), ...]
    # Baseline:
    # 0–10 min = 100
    # 10–20 min = 80
    # 20–30 min = 60
    # 30–45 min = 35
    # > 45 min = 10
    travel_time_thresholds: List[Tuple[float, float]] = Field(
        default_factory=lambda: [
            (10.0, 100.0),
            (20.0, 80.0),
            (30.0, 60.0),
            (45.0, 35.0),
            (float("inf"), 10.0),
        ]
    )

    # 5. Service Desert Classifications:
    # 80–100 = Well Served
    # 60–79 = Adequate
    # 40–59 = At Risk
    # 20–39 = Underserved
    # 0–19 = Critical Desert
    desert_classifications: List[Tuple[float, str]] = Field(
        default_factory=lambda: [
            (80.0, "Well Served"),
            (60.0, "Adequate"),
            (40.0, "At Risk"),
            (20.0, "Underserved"),
            (0.0, "Critical Desert"),
        ]
    )

    @model_validator(mode="after")
    def validate_weights_sum(self):
        total = (
            self.travel_time_weight
            + self.availability_weight
            + self.capacity_weight
            + self.transport_weight
            + self.equity_weight
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Accessibility weights must sum to 1.0 (100%), got {total:.4f}")
        return self


# Default singleton instance
default_analytics_config = AnalyticsConfig()
