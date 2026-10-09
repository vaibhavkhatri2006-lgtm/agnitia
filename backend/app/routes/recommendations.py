"""
Recommendation Scoring Engine API routes (Stage 4B).
Computes multi-factor scores and returns deterministic priority rankings for candidate locations.
"""
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.decision.recommendation import (
    default_recommendation_service,
    RecommendationConfig,
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    ScoredCandidateResponse,
    ExcludedCandidateResponse,
    FactorValues,
    FactorWeights,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.post(
    "",
    response_model=RecommendationResponse,
    summary="Compute ranked candidate location recommendations (POST)",
)
def create_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Evaluates, scores, and ranks candidate intervention locations for a specified service type.
    Normalizes 7 multi-dimensional criteria (Gap Severity, Population, Travel Need,
    Capacity Pressure, Equity Need, Connectivity, and Data Confidence).
    """
    try:
        norm_type = default_recommendation_service.validate_service_type(payload.service_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Optional custom weights handling
    cfg = None
    if payload.weights:
        try:
            cfg = RecommendationConfig(**payload.weights)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recommendation weights: {str(exc)}",
            )

    result = default_recommendation_service.rank_candidates(
        db=db,
        service_type=norm_type,
        area_id=payload.area_id,
        min_gap_threshold=payload.min_gap_threshold,
        config=cfg,
    )

    ranked_out = [
        ScoredCandidateResponse(
            candidate_id=item.candidate_id,
            service_type=item.service_type,
            rank=item.rank,
            recommendation_score=item.recommendation_score,
            latitude=item.latitude,
            longitude=item.longitude,
            area_id=item.area_id,
            area_name=item.area_name,
            population=item.population,
            strategy=item.strategy,
            confidence=item.confidence,
            expected_gain_pts=getattr(item, "expected_gain_pts", None),
            factor_values=FactorValues(**item.factor_values),
            factor_weights=FactorWeights(**item.factor_weights),
            reasons=item.reasons,
        )
        for item in result["ranked_candidates"]
    ]

    excluded_out = [
        ExcludedCandidateResponse(
            candidate_id=item["candidate_id"],
            service_type=item["service_type"],
            area_id=item["area_id"],
            area_name=item["area_name"],
            validity_status=item["validity_status"],
            rejection_reason=item.get("rejection_reason"),
        )
        for item in result["excluded_candidates"]
    ]

    return RecommendationResponse(
        service_type=norm_type,
        total_candidates_evaluated=result["total_candidates_evaluated"],
        valid_candidates_scored=result["valid_candidates_scored"],
        excluded_candidates_count=result["excluded_candidates_count"],
        weights_used=FactorWeights(**result["weights_used"]),
        ranked_candidates=ranked_out,
        excluded_candidates=excluded_out,
    )


@router.get(
    "",
    response_model=RecommendationResponse,
    summary="Compute ranked candidate location recommendations (GET)",
)
def get_recommendations(
    service_type: str = Query(
        ...,
        description="Target service category: 'healthcare', 'education', 'transport', 'water', 'market'",
    ),
    area_id: Optional[int] = Query(
        None,
        description="Optional area ID filter",
    ),
    min_gap_threshold: float = Query(
        20.0,
        ge=0.0,
        le=100.0,
        description="Minimum gap score threshold",
    ),
    db: Session = Depends(get_db),
):
    """
    GET endpoint retrieving ranked candidate location recommendations.
    """
    req = RecommendationRequest(
        service_type=service_type,
        area_id=area_id,
        min_gap_threshold=min_gap_threshold,
    )
    return create_recommendations(payload=req, db=db)
