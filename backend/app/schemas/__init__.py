"""Pydantic request and response schemas."""
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RoleResponse, RoleVerificationResponse
from app.schemas.errors import HTTPErrorResponse, ErrorDetail
from app.schemas.analytics import (
    ServicePressureResponse,
    CategoryAnalyticsResponse,
    AreaSummaryAnalyticsResponse,
    ServiceDesertItemResponse,
    AnalyticsConfigResponse,
)

from app.schemas.decision import (
    CandidateLocationResponse,
    CandidateGenerationRequest,
    CandidateGenerationResponse,
)

from app.schemas.recommendation import (
    FactorValues,
    FactorWeights,
    ScoredCandidateResponse,
    ExcludedCandidateResponse,
    RecommendationRequest,
    RecommendationResponse,
)

from app.schemas.simulation import (
    SimulationRequest,
    SimulationStateMetrics,
    SimulationImpactMetrics,
    TargetAreaImpact,
    SimulationResponse,
)

from app.schemas.investment import (
    InvestmentPriorityRequest,
    RankedInvestmentItem,
    InvestmentPriorityResponse,
)

from app.schemas.resilience import (
    FailureSimulationRequest,
    AffectedAreaFailureItem,
    FailureSimulationResponse,
)

from app.schemas.future_risk import (
    FutureRiskRequest,
    AreaFutureRiskItem,
    FutureRiskResponse,
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "RoleResponse",
    "RoleVerificationResponse",
    "HTTPErrorResponse",
    "ErrorDetail",
    "ServicePressureResponse",
    "CategoryAnalyticsResponse",
    "AreaSummaryAnalyticsResponse",
    "ServiceDesertItemResponse",
    "AnalyticsConfigResponse",
    "CandidateLocationResponse",
    "CandidateGenerationRequest",
    "CandidateGenerationResponse",
    "FactorValues",
    "FactorWeights",
    "ScoredCandidateResponse",
    "ExcludedCandidateResponse",
    "RecommendationRequest",
    "RecommendationResponse",
    "SimulationRequest",
    "SimulationStateMetrics",
    "SimulationImpactMetrics",
    "TargetAreaImpact",
    "SimulationResponse",
    "InvestmentPriorityRequest",
    "RankedInvestmentItem",
    "InvestmentPriorityResponse",
    "FailureSimulationRequest",
    "AffectedAreaFailureItem",
    "FailureSimulationResponse",
    "FutureRiskRequest",
    "AreaFutureRiskItem",
    "FutureRiskResponse",
]
