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
from app.analytics.multiscale import default_multiscale_service
from app.schemas.multiscale import (
    GeographicHierarchyNode,
    HierarchyValidationReport,
    HierarchyRelationshipValidationRequest,
    HierarchyRelationshipValidationResponse,
    MultiScaleScopesResponse,
)

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
    "/scopes",
    response_model=MultiScaleScopesResponse,
    summary="Discover supported and unavailable geographic scales",
)
def get_geographic_scopes(
    db: Session = Depends(get_db),
):
    """
    Returns all recognized geographic scales (Local, Neighbourhood, Ward, City, Region, Country, Global)
    and their active availability status in the current dataset without inventing synthetic data.
    """
    return default_multiscale_service.get_scope_availability(db)


@router.get(
    "/hierarchy",
    response_model=List[GeographicHierarchyNode],
    summary="Get full administrative geographic hierarchy tree",
)
def get_geographic_hierarchy(
    db: Session = Depends(get_db),
):
    """
    Returns the complete recursive geographic hierarchy from top-level root areas down to leaf units.
    """
    return default_multiscale_service.build_hierarchy_tree(db)


@router.get(
    "/hierarchy/validate",
    response_model=HierarchyValidationReport,
    summary="Validate parent-child geographic hierarchy integrity",
)
def validate_geographic_hierarchy(
    db: Session = Depends(get_db),
):
    """
    Audits the database for parent-child relationship integrity:
    verifies parent existence, detects orphaned references, circular loops, and hierarchy scale ordering.
    """
    return default_multiscale_service.validate_hierarchy_integrity(db)


@router.post(
    "/hierarchy/validate-relationship",
    response_model=HierarchyRelationshipValidationResponse,
    summary="Validate relationship between parent and child administrative scales",
)
def validate_geographic_relationship(
    payload: HierarchyRelationshipValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validates whether a proposed parent-child linkage conforms to civic hierarchy scale ordering rules.
    """
    p_type = payload.parent_type
    c_type = payload.child_type

    # If IDs are provided, lookup actual area types
    if payload.parent_id and not p_type:
        p_area = db.query(GeographicArea).filter_by(id=payload.parent_id).first()
        if p_area:
            p_type = p_area.area_type
        else:
            return HierarchyRelationshipValidationResponse(
                is_valid=False,
                reason=f"Parent area with id={payload.parent_id} does not exist in database.",
                parent_type=None,
                child_type=c_type,
            )

    if payload.child_id and not c_type:
        c_area = db.query(GeographicArea).filter_by(id=payload.child_id).first()
        if c_area:
            c_type = c_area.area_type
        else:
            return HierarchyRelationshipValidationResponse(
                is_valid=False,
                reason=f"Child area with id={payload.child_id} does not exist in database.",
                parent_type=p_type,
                child_type=None,
            )

    is_valid, reason = default_multiscale_service.validate_relationship_types(p_type, c_type)
    return HierarchyRelationshipValidationResponse(
        is_valid=is_valid,
        reason=reason,
        parent_type=p_type,
        child_type=c_type,
    )


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
