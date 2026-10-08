"""
Service & Facility API routes for CivicPulse.
Provides access to cataloged civic service facilities and categories for maps,
filter dropdowns, and resilience simulation targets.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Service, ServiceCategory, GeographicArea
from app.schemas.infrastructure import ServiceItem, ServiceCategoryItem
from app.schemas.geojson import (
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.analytics.geojson import point_to_geojson_dict

router = APIRouter(prefix="/services", tags=["Services & Infrastructure"])


@router.get(
    "/categories",
    response_model=List[ServiceCategoryItem],
    summary="List all supported service categories",
)
def get_service_categories(
    db: Session = Depends(get_db),
):
    """
    Returns all active service categories (e.g. healthcare, education, transport, water, market)
    along with their standard planning distance and analytical weights.
    """
    categories = (
        db.query(ServiceCategory)
        .filter(ServiceCategory.is_active == True)
        .order_by(ServiceCategory.id)
        .all()
    )
    return [
        ServiceCategoryItem(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            icon=cat.icon,
            is_active=cat.is_active,
        )
        for cat in categories
    ]


@router.get(
    "/geojson",
    response_model=GeoJSONFeatureCollection,
    summary="Get all civic facilities as RFC 7946 GeoJSON Point FeatureCollection",
)
def get_services_geojson(
    category_code: Optional[str] = Query(
        None,
        description="Filter by service category code (e.g. healthcare, education, transport, water, market)",
    ),
    area_id: Optional[int] = Query(
        None,
        description="Filter by host geographic area ID",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by operational status (operational, degraded, temporarily_unavailable, closed)",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns civic facilities formatted as standard GeoJSON Point features.
    Ideal for direct consumption by Leaflet marker layers.
    """
    query = db.query(Service).join(ServiceCategory)

    if category_code:
        query = query.filter(ServiceCategory.code == category_code.lower())

    if area_id is not None:
        query = query.filter(Service.area_id == area_id)

    if status_filter:
        query = query.filter(Service.status == status_filter.lower())

    services = query.order_by(Service.id).all()
    features = []

    for s in services:
        geom_dict = point_to_geojson_dict(s.latitude, s.longitude)
        geom_obj = GeoJSONGeometry(**geom_dict) if geom_dict else None

        cap_val = s.capacity_record.capacity if s.capacity_record else None
        load_val = s.capacity_record.current_load if s.capacity_record else None

        props = {
            "id": s.id,
            "name": s.name,
            "category_id": s.category_id,
            "category_code": s.category.code if s.category else "unknown",
            "category_name": s.category.name if s.category else "Unknown",
            "area_id": s.area_id,
            "area_name": s.area.name if s.area else None,
            "latitude": float(s.latitude),
            "longitude": float(s.longitude),
            "status": s.status,
            "source_type": s.source_type,
            "verification_status": s.verification_status,
            "confidence_score": float(s.confidence_score),
            "capacity": cap_val,
            "current_load": load_val,
            "operating_hours": s.operating_hours,
        }

        features.append(
            GeoJSONFeature(
                type="Feature",
                id=s.id,
                geometry=geom_obj,
                properties=props,
            )
        )

    return GeoJSONFeatureCollection(type="FeatureCollection", features=features)


@router.get(
    "",
    response_model=List[ServiceItem],
    summary="List cataloged civic service facilities with optional filters",
)
def get_services(
    category_code: Optional[str] = Query(
        None,
        description="Filter by service category code (e.g. healthcare, education, transport, water, market)",
    ),
    area_id: Optional[int] = Query(
        None,
        description="Filter by host geographic area ID",
    ),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by operational status (operational, degraded, temporarily_unavailable, closed)",
    ),
    db: Session = Depends(get_db),
):
    """
    Lists cataloged civic services. Allows the frontend to render facility pins on maps
    and populate facility selection controls.
    """
    query = db.query(Service).join(ServiceCategory)

    if category_code:
        query = query.filter(ServiceCategory.code == category_code.lower())

    if area_id is not None:
        query = query.filter(Service.area_id == area_id)

    if status_filter:
        query = query.filter(Service.status == status_filter.lower())

    services = query.order_by(Service.id).all()
    results = []

    for s in services:
        cap_val = s.capacity_record.capacity if s.capacity_record else None
        load_val = s.capacity_record.current_load if s.capacity_record else None
        results.append(
            ServiceItem(
                id=s.id,
                name=s.name,
                category_id=s.category_id,
                category_code=s.category.code if s.category else "unknown",
                category_name=s.category.name if s.category else "Unknown",
                area_id=s.area_id,
                area_name=s.area.name if s.area else None,
                latitude=float(s.latitude),
                longitude=float(s.longitude),
                status=s.status,
                source_type=s.source_type,
                verification_status=s.verification_status,
                confidence_score=float(s.confidence_score),
                capacity=cap_val,
                current_load=load_val,
                operating_hours=s.operating_hours,
            )
        )

    return results


@router.get(
    "/{service_id}",
    response_model=ServiceItem,
    summary="Get details for a specific civic service facility",
)
def get_service_by_id(
    service_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves full details for a single civic service facility by its ID.
    """
    s = db.query(Service).filter(Service.id == service_id).first()
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with id {service_id} not found",
        )

    cap_val = s.capacity_record.capacity if s.capacity_record else None
    load_val = s.capacity_record.current_load if s.capacity_record else None

    return ServiceItem(
        id=s.id,
        name=s.name,
        category_id=s.category_id,
        category_code=s.category.code if s.category else "unknown",
        category_name=s.category.name if s.category else "Unknown",
        area_id=s.area_id,
        area_name=s.area.name if s.area else None,
        latitude=float(s.latitude),
        longitude=float(s.longitude),
        status=s.status,
        source_type=s.source_type,
        verification_status=s.verification_status,
        confidence_score=float(s.confidence_score),
        capacity=cap_val,
        current_load=load_val,
        operating_hours=s.operating_hours,
    )
