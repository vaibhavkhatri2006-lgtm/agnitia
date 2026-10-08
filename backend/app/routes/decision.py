"""
Decision & Candidate Engine API routes (Stage 4A).
Generates and inspects deterministic candidate locations for new civic facilities.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.decision.candidates import default_candidate_service
from app.decision.investment import default_investment_service
from app.decision.resilience import default_resilience_service
from app.decision.future_risk import default_future_risk_service
from app.decision.simulation import default_simulation_service
from app.schemas.decision import (
    CandidateGenerationRequest,
    CandidateGenerationResponse,
    CandidateLocationResponse,
)
from app.schemas.investment import (
    InvestmentPriorityRequest,
    InvestmentPriorityResponse,
)
from app.schemas.resilience import (
    FailureSimulationRequest,
    FailureSimulationResponse,
)
from app.schemas.future_risk import (
    FutureRiskRequest,
    FutureRiskResponse,
)
from app.schemas.simulation import (
    ScenarioComparisonRequest,
    ScenarioComparisonResponse,
)

router = APIRouter(prefix="/decision", tags=["Decision Engine"])


@router.get(
    "/candidates",
    response_model=CandidateGenerationResponse,
    summary="Generate candidate locations for a civic service type",
)
def get_candidate_locations(
    service_type: str = Query(
        ...,
        description="Target service category code: 'healthcare', 'education', 'transport', 'water', 'market'",
    ),
    min_gap_threshold: float = Query(
        20.0,
        ge=0.0,
        le=100.0,
        description="Minimum gap score threshold for an area to qualify",
    ),
    max_accessibility: float = Query(
        80.0,
        ge=0.0,
        le=100.0,
        description="Maximum accessibility score (excludes areas already sufficiently served)",
    ),
    include_rejected: bool = Query(
        False,
        description="Whether to include rejected/invalid candidate points in response",
    ),
    db: Session = Depends(get_db),
):
    """
    Identifies and validates deterministic candidate locations for new civic facilities
    based on underserved area analytics, population demand, and spatial coverage gaps.
    """
    try:
        norm_type = default_candidate_service.validate_service_type(service_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    candidates = default_candidate_service.generate_candidates_for_service(
        db=db,
        service_type=norm_type,
        min_gap_threshold=min_gap_threshold,
        max_accessibility=max_accessibility,
        include_rejected=include_rejected,
    )

    valid_count = sum(1 for c in candidates if c.validity_status == "valid")
    rejected_count = sum(1 for c in candidates if c.validity_status != "valid")

    return CandidateGenerationResponse(
        service_type=norm_type,
        total_candidates=len(candidates),
        valid_candidates_count=valid_count,
        rejected_candidates_count=rejected_count,
        candidates=[CandidateLocationResponse(**c.to_dict()) for c in candidates],
    )


@router.post(
    "/candidates/generate",
    response_model=CandidateGenerationResponse,
    summary="Generate candidate locations from JSON request body",
)
def generate_candidate_locations(
    payload: CandidateGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    POST endpoint generating candidate locations with full configuration options.
    """
    try:
        norm_type = default_candidate_service.validate_service_type(payload.service_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    candidates = default_candidate_service.generate_candidates_for_service(
        db=db,
        service_type=norm_type,
        min_gap_threshold=payload.min_gap_threshold,
        max_accessibility=payload.max_accessibility,
        include_rejected=payload.include_rejected,
    )

    valid_count = sum(1 for c in candidates if c.validity_status == "valid")
    rejected_count = sum(1 for c in candidates if c.validity_status != "valid")

    return CandidateGenerationResponse(
        service_type=norm_type,
        total_candidates=len(candidates),
        valid_candidates_count=valid_count,
        rejected_candidates_count=rejected_count,
        candidates=[CandidateLocationResponse(**c.to_dict()) for c in candidates],
    )


# --- 1. Investment Priority Endpoints (Stage 4D Task 1) ---

@router.post(
    "/investment-priorities",
    response_model=InvestmentPriorityResponse,
    summary="Compute ranked investment priorities for civic interventions (POST)",
)
def compute_investment_priorities_post(
    payload: InvestmentPriorityRequest,
    db: Session = Depends(get_db),
):
    """
    Ranks intervention opportunities by strategic civic investment priority
    balancing urgency, population scale, equity, and expected accessibility impact.
    """
    try:
        result = default_investment_service.rank_investment_priorities(
            db=db,
            service_type=payload.service_type,
            min_gap_threshold=payload.min_gap_threshold,
            max_results=payload.max_results,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/investment-priorities",
    response_model=InvestmentPriorityResponse,
    summary="Compute ranked investment priorities for civic interventions (GET)",
)
def compute_investment_priorities_get(
    service_type: Optional[str] = Query(
        None,
        description="Optional filter by service type (healthcare, education, transport, water, market)",
    ),
    min_gap_threshold: float = Query(
        20.0,
        ge=0.0,
        le=100.0,
        description="Minimum gap score threshold",
    ),
    max_results: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum ranked results to return",
    ),
    db: Session = Depends(get_db),
):
    """
    GET variant for retrieving ranked investment priorities.
    """
    try:
        result = default_investment_service.rank_investment_priorities(
            db=db,
            service_type=service_type,
            min_gap_threshold=min_gap_threshold,
            max_results=max_results,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# --- 2. Failure / Resilience Simulation Endpoints (Stage 4D Task 2) ---

@router.post(
    "/failure-simulation",
    response_model=FailureSimulationResponse,
    summary="Simulate facility outage and measure systemic resilience (POST)",
)
def simulate_facility_failure_post(
    payload: FailureSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulates a facility outage/failure in-memory to calculate affected population,
    accessibility drop, coverage collapse, and identify single points of failure.
    """
    try:
        result = default_resilience_service.simulate_service_failure(
            db=db,
            service_id=payload.service_id,
            scope=payload.scope,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/failure-simulation",
    response_model=FailureSimulationResponse,
    summary="Simulate facility outage and measure systemic resilience (GET)",
)
def simulate_facility_failure_get(
    service_id: int = Query(
        ...,
        description="ID of the civic facility to simulate outage for",
    ),
    scope: Optional[str] = Query(
        "city",
        description="Analysis scope: 'city', 'neighbourhoods', or area ID",
    ),
    db: Session = Depends(get_db),
):
    """
    GET variant for simulating facility failure and measuring systemic resilience.
    """
    try:
        result = default_resilience_service.simulate_service_failure(
            db=db,
            service_id=service_id,
            scope=scope,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# --- 3. Future-Risk Foundation Endpoints (Stage 4D Task 3) ---

@router.post(
    "/future-risk",
    response_model=FutureRiskResponse,
    summary="Estimate future civic risk under demand growth projections (POST)",
)
def estimate_future_risk_post(
    payload: FutureRiskRequest,
    db: Session = Depends(get_db),
):
    """
    Calculates deterministic forward-looking civic risk projections
    under configurable population demand growth.
    """
    try:
        result = default_future_risk_service.estimate_future_risk(
            db=db,
            growth_rate_pct=payload.growth_rate_pct,
            time_horizon_years=payload.time_horizon_years,
            service_type=payload.service_type,
            area_id=payload.area_id,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/future-risk",
    response_model=FutureRiskResponse,
    summary="Estimate future civic risk under demand growth projections (GET)",
)
def estimate_future_risk_get(
    growth_rate_pct: float = Query(
        15.0,
        ge=0.0,
        le=100.0,
        description="Projected demand growth percentage",
    ),
    time_horizon_years: int = Query(
        5,
        ge=1,
        le=30,
        description="Projection horizon in years",
    ),
    service_type: Optional[str] = Query(
        None,
        description="Optional filter by service category",
    ),
    area_id: Optional[int] = Query(
        None,
        description="Optional filter by area ID",
    ),
    db: Session = Depends(get_db),
):
    """
    GET variant for estimating future civic risk under demand growth projections.
    """
    try:
        result = default_future_risk_service.estimate_future_risk(
            db=db,
            growth_rate_pct=growth_rate_pct,
            time_horizon_years=time_horizon_years,
            service_type=service_type,
            area_id=area_id,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# --- Scenario Comparison Endpoints (Stage 9 Scenario Lab) ---

@router.post(
    "/scenarios",
    response_model=ScenarioComparisonResponse,
    summary="Compare multi-facility intervention scenarios (POST)",
)
def compare_scenarios_decision_post(
    payload: ScenarioComparisonRequest,
    db: Session = Depends(get_db),
):
    """
    Executes Scenario Lab comparative analysis:
    Compares baseline current state against 1-facility and multiple-facility intervention scenarios.
    Returns consistent, deterministic metrics and impact deltas without modifying the database.
    """
    try:
        scenarios_input = [s.model_dump() for s in payload.scenarios] if payload.scenarios else None
        result = default_simulation_service.compare_scenarios(
            db=db,
            service_type=payload.service_type,
            scope=payload.scope or "city",
            scenarios=scenarios_input,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario comparison failed: {str(exc)}",
        )


@router.get(
    "/scenarios",
    response_model=ScenarioComparisonResponse,
    summary="Compare multi-facility intervention scenarios (GET)",
)
def compare_scenarios_decision_get(
    service_type: str = Query(
        "healthcare",
        description="Target service type: healthcare, education, transport, water, market",
    ),
    scope: Optional[str] = Query(
        "city",
        description="Analysis scope: 'city', 'neighbourhoods', or area ID",
    ),
    db: Session = Depends(get_db),
):
    """
    GET variant for Scenario Lab comparison across baseline, 1 new facility, and 2 new facilities.
    """
    try:
        result = default_simulation_service.compare_scenarios(
            db=db,
            service_type=service_type,
            scope=scope or "city",
            scenarios=None,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario comparison failed: {str(exc)}",
        )

