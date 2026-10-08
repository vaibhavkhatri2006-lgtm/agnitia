"""
Operational Mode API Route for CivicPulse.
Provides endpoints to inspect and toggle between DEMO MODE (synthetic dataset)
and REAL DATA MODE (live OpenStreetMap ingestion with verified provenance).
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.real_data import CivicPulseModeResponse, CivicPulseModeUpdateRequest
from app.services.mode_service import get_mode_metadata, set_current_mode

router = APIRouter(prefix="/mode", tags=["System Mode"])


@router.get(
    "",
    response_model=CivicPulseModeResponse,
    summary="Get current CivicPulse operational mode (demo or real)",
)
def get_operational_mode():
    """
    Returns the active operational data mode of the platform.
    - 'demo': Uses deterministic synthetic data for safe offline evaluation and walkthroughs.
    - 'real': Ingests live OpenStreetMap geospatial data and preserves public census population without fabrication.
    """
    meta = get_mode_metadata()
    return CivicPulseModeResponse(**meta)


@router.post(
    "",
    response_model=CivicPulseModeResponse,
    summary="Toggle CivicPulse operational mode between demo and real",
)
def set_operational_mode(payload: CivicPulseModeUpdateRequest):
    """
    Switches CivicPulse between DEMO MODE and REAL DATA MODE at runtime.
    Validates the target mode and returns the updated mode configuration.
    """
    try:
        set_current_mode(payload.mode)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    meta = get_mode_metadata()
    return CivicPulseModeResponse(**meta)
