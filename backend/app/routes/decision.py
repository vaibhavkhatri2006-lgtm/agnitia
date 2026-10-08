"""
Decision & Candidate Engine API routes (Stage 4A).
Generates and inspects deterministic candidate locations for new civic facilities.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.decision.candidates import default_candidate_service
from app.schemas.decision import (
    CandidateGenerationRequest,
    CandidateGenerationResponse,
    CandidateLocationResponse,
)

router = APIRouter(prefix="/decision", tags=["Decision & Candidate Engine"])


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
