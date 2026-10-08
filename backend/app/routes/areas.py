"""
Geographic Area & Locality API routes for CivicPulse.
Provides access to administrative boundaries, wards, and neighbourhoods for UI map layers,
boundary outlines, and locality pickers.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GeographicArea
from app.schemas.infrastructure import GeographicAreaItem

router = APIRouter(prefix="/areas", tags=["Localities & Geographic Areas"])


@router.get(
    "",
    response_model=List[GeographicAreaItem],
    summary="List geographic localities and administrative areas",
)
def get_areas(
    area_type: Optional[str] = Query(
        None,
        description="Filter by area type (city, ward, neighbourhood)",
    ),
    parent_id: Optional[int] = Query(
        None,
        description="Filter by parent geographic area ID",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns administrative areas and localities for frontend maps, dropdowns, and dashboards.
    """
    query = db.query(GeographicArea)

    if area_type:
        query = query.filter(GeographicArea.area_type == area_type.lower())

    if parent_id is not None:
        query = query.filter(GeographicArea.parent_id == parent_id)

    areas = query.order_by(GeographicArea.id).all()
    return [
        GeographicAreaItem(
            id=a.id,
            name=a.name,
            area_type=a.area_type,
            parent_id=a.parent_id,
            population=int(a.population),
        )
        for a in areas
    ]


@router.get(
    "/{area_id}",
    response_model=GeographicAreaItem,
    summary="Get details for a specific geographic locality",
)
def get_area_by_id(
    area_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves metadata for a specific geographic area by its ID.
    """
    area = db.query(GeographicArea).filter(GeographicArea.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geographic area with id {area_id} not found",
        )

    return GeographicAreaItem(
        id=area.id,
        name=area.name,
        area_type=area.area_type,
        parent_id=area.parent_id,
        population=int(area.population),
    )
