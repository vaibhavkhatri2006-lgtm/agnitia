"""
Geographic Area & Locality API routes for CivicPulse.
Provides access to administrative boundaries, wards, and neighbourhoods for UI map layers,
GeoJSON polygon boundary rendering, and locality pickers.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GeographicArea
from app.schemas.infrastructure import GeographicAreaItem
from app.schemas.geojson import (
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.analytics.geojson import geometry_to_geojson_dict
from app.analytics.engine import default_analytics_engine

router = APIRouter(prefix="/areas", tags=["Localities & Geographic Areas"])


@router.get(
    "/geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Get all geographic locality boundaries as RFC 7946 GeoJSON FeatureCollection",
)
def get_areas_geojson(
    area_type: Optional[str] = Query(
        None,
        description="Filter by area type (city, ward, neighbourhood)",
    ),
    parent_id: Optional[int] = Query(
        None,
        description="Filter by parent geographic area ID",
    ),
    include_analytics: bool = Query(
        True,
        description="Whether to attach composite accessibility and gap scores to feature properties",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns boundaries and attributes of geographic areas formatted as a standard GeoJSON FeatureCollection.
    Ideal for direct consumption by frontend Leaflet or MapLibre GeoJSON layers.
    """
    query = db.query(GeographicArea)

    if area_type:
        query = query.filter(GeographicArea.area_type == area_type.lower())

    if parent_id is not None:
        query = query.filter(GeographicArea.parent_id == parent_id)

    areas = query.order_by(GeographicArea.id).all()
    features = []

    for a in areas:
        geom_dict = geometry_to_geojson_dict(a.geometry)
        geom_obj = GeoJSONGeometry(**geom_dict) if geom_dict else None

        props = {
            "id": a.id,
            "name": a.name,
            "area_type": a.area_type,
            "parent_id": a.parent_id,
            "population": int(a.population),
        }

        if include_analytics:
            analytics = default_analytics_engine.analyze_area_overall(db, a)
            props["accessibility_score"] = analytics["composite_accessibility_score"]
            props["gap_score"] = analytics["composite_gap_score"]
            props["desert_classification"] = analytics["composite_desert_classification"]
            props["categories_evaluated"] = analytics["categories_evaluated"]

        features.append(
            GeoJSONFeature(
                type="Feature",
                id=a.id,
                geometry=geom_obj,
                properties=props,
            )
        )

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


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
    "/{area_id}/geojson",
    response_model=GeoJSONFeature,
    summary="Get a single locality boundary and properties as GeoJSON Feature",
)
def get_area_geojson_by_id(
    area_id: int,
    include_analytics: bool = Query(
        True,
        description="Whether to attach composite accessibility and gap scores to feature properties",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns a single locality boundary formatted as an RFC 7946 GeoJSON Feature.
    """
    area = db.query(GeographicArea).filter(GeographicArea.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geographic area with id {area_id} not found",
        )

    geom_dict = geometry_to_geojson_dict(area.geometry)
    geom_obj = GeoJSONGeometry(**geom_dict) if geom_dict else None

    props = {
        "id": area.id,
        "name": area.name,
        "area_type": area.area_type,
        "parent_id": area.parent_id,
        "population": int(area.population),
    }

    if include_analytics:
        analytics = default_analytics_engine.analyze_area_overall(db, area)
        props["accessibility_score"] = analytics["composite_accessibility_score"]
        props["gap_score"] = analytics["composite_gap_score"]
        props["desert_classification"] = analytics["composite_desert_classification"]
        props["categories_evaluated"] = analytics["categories_evaluated"]

    return GeoJSONFeature(
        type="Feature",
        id=area.id,
        geometry=geom_obj,
        properties=props,
    )


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
