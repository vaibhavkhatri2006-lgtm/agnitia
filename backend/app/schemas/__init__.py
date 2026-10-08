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
    ScenarioFacilityInput,
    ScenarioDefinition,
    ScenarioComparisonRequest,
    ScenarioImpactVsBaseline,
    ScenarioResultItem,
    ScenarioComparisonResponse,
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

from app.schemas.infrastructure import (
    ServiceCategoryItem,
    ServiceItem,
    GeographicAreaItem,
)

from app.schemas.geojson import (
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)

from app.schemas.rankings import (
    UnderservedAreaRankingItem,
    UnderservedRankingsResponse,
)

from app.schemas.reports import (
    ReportCreateRequest,
    ReportVerificationRequest,
    ReportVerificationItem,
    AuditLogItem,
    ReportResponse,
    ReportDetailResponse,
)

from app.schemas.planner import (
    PlannerUnderservedAreaItem,
    PlannerUnderservedRankingsResponse,
    PlannerServiceComparisonItem,
    PlannerServiceComparisonResponse,
    PlannerCapacityPressureItem,
    PlannerCapacityPressureResponse,
    PlannerEquityRealityGapResponse,
    PlannerCandidateInfo,
    PlannerExpectedImpact,
    PlannerRecommendationItem,
    PlannerRecommendationsResponse,
    PlannerOverviewResponse,
)
from app.schemas.multiscale import (
    GeographicHierarchyNode,
    HierarchyValidationReport,
    HierarchyRelationshipValidationRequest,
    HierarchyRelationshipValidationResponse,
    ScopeAvailabilityItem,
    MultiScaleScopesResponse,
    MultiScaleAreaSummary,
    MultiScaleAnalyticsResponse,
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
    "ScenarioFacilityInput",
    "ScenarioDefinition",
    "ScenarioComparisonRequest",
    "ScenarioImpactVsBaseline",
    "ScenarioResultItem",
    "ScenarioComparisonResponse",
    "InvestmentPriorityRequest",
    "RankedInvestmentItem",
    "InvestmentPriorityResponse",
    "FailureSimulationRequest",
    "AffectedAreaFailureItem",
    "FailureSimulationResponse",
    "FutureRiskRequest",
    "AreaFutureRiskItem",
    "FutureRiskResponse",
    "ServiceCategoryItem",
    "ServiceItem",
    "GeographicAreaItem",
    "GeoJSONGeometry",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "UnderservedAreaRankingItem",
    "UnderservedRankingsResponse",
    "ReportCreateRequest",
    "ReportVerificationRequest",
    "ReportVerificationItem",
    "AuditLogItem",
    "ReportResponse",
    "ReportDetailResponse",
    "PlannerUnderservedAreaItem",
    "PlannerUnderservedRankingsResponse",
    "PlannerServiceComparisonItem",
    "PlannerServiceComparisonResponse",
    "PlannerCapacityPressureItem",
    "PlannerCapacityPressureResponse",
    "PlannerEquityRealityGapResponse",
    "PlannerCandidateInfo",
    "PlannerExpectedImpact",
    "PlannerRecommendationItem",
    "PlannerRecommendationsResponse",
    "PlannerOverviewResponse",
    "GeographicHierarchyNode",
    "HierarchyValidationReport",
    "HierarchyRelationshipValidationRequest",
    "HierarchyRelationshipValidationResponse",
    "ScopeAvailabilityItem",
    "MultiScaleScopesResponse",
    "MultiScaleAreaSummary",
    "MultiScaleAnalyticsResponse",
]
