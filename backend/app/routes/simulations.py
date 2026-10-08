"""
Intervention Simulation API routes (Stage 4C).
Computes in-memory what-if simulations of civic facility interventions, comparing
Before vs After states and calculating measurable access improvements.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.decision.simulation import default_simulation_service
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
)

router = APIRouter(prefix="/simulations", tags=["Intervention Simulation"])


@router.post(
    "",
    response_model=SimulationResponse,
    summary="Simulate adding a civic service at a proposed location (POST)",
)
def create_simulation(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Executes a deterministic what-if simulation for adding a proposed civic facility.
    Compares baseline accessibility against post-intervention access without modifying
    the official database.
    """
    try:
        result = default_simulation_service.simulate_intervention(
            db=db,
            service_type=payload.service_type,
            candidate_id=payload.candidate_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            scope=payload.scope,
            proposed_name=payload.proposed_name,
            proposed_capacity=payload.proposed_capacity,
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
            detail=f"Simulation failed: {str(exc)}",
        )


@router.get(
    "",
    response_model=SimulationResponse,
    summary="Simulate adding a civic service at a proposed location (GET)",
)
def get_simulation(
    service_type: str = Query(
        ...,
        description="Service type: healthcare, education, transport, water, market",
    ),
    candidate_id: Optional[str] = Query(
        None,
        description="Candidate ID from Stage 4A/4B (e.g., 'cand-healthcare-9-centroid')",
    ),
    latitude: Optional[float] = Query(
        None,
        ge=-90.0,
        le=90.0,
        description="Proposed facility latitude (-90 to 90)",
    ),
    longitude: Optional[float] = Query(
        None,
        ge=-180.0,
        le=180.0,
        description="Proposed facility longitude (-180 to 180)",
    ),
    scope: Optional[str] = Query(
        "city",
        description="Analysis scope: 'city', 'neighbourhoods', or area ID",
    ),
    proposed_capacity: Optional[int] = Query(
        5000,
        ge=1,
        description="Proposed facility capacity",
    ),
    db: Session = Depends(get_db),
):
    """
    Query-parameter variant of what-if intervention simulation.
    """
    try:
        result = default_simulation_service.simulate_intervention(
            db=db,
            service_type=service_type,
            candidate_id=candidate_id,
            latitude=latitude,
            longitude=longitude,
            scope=scope,
            proposed_capacity=proposed_capacity,
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
            detail=f"Simulation failed: {str(exc)}",
        )
