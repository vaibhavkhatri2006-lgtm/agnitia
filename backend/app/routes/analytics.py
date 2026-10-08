"""
Geospatial and Analytics Engine API routes for CivicPulse.
Provides deterministic calculations for Accessibility Scores, Gap Scores,
Service Desert Classifications, Service Pressure, Equity Scores, and Reality Gap metrics.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GeographicArea, ServiceCategory
from app.analytics.engine import default_analytics_engine
from app.analytics.config import default_analytics_config
from app.schemas.analytics import (
    AnalyticsConfigResponse,
    AreaSummaryAnalyticsResponse,
    CategoryAnalyticsResponse,
    ServiceDesertItemResponse,
)
from app.schemas.rankings import (
    UnderservedAreaRankingItem,
    UnderservedRankingsResponse,
)

router = APIRouter(prefix="/analytics", tags=["Geospatial & Analytics Engine"])


@router.get(
    "/config",
    response_model=AnalyticsConfigResponse,
    summary="Get current analytics weights and classification thresholds",
)
def get_analytics_config():
    """
    Returns the central configuration used by the analytics engine:
    - Accessibility score component weights (travel time, availability, capacity, transport, equity)
    - Travel speed assumptions
    - Service state availability mappings
    - Travel time score thresholds
    - Service desert classifications
    """
    cfg = default_analytics_config
    return AnalyticsConfigResponse(
        travel_time_weight=cfg.travel_time_weight,
        availability_weight=cfg.availability_weight,
        capacity_weight=cfg.capacity_weight,
        transport_weight=cfg.transport_weight,
        equity_weight=cfg.equity_weight,
        travel_speeds_kmh=cfg.travel_speeds_kmh,
        availability_scores=cfg.availability_scores,
        travel_time_thresholds=[list(item) for item in cfg.travel_time_thresholds],
        desert_classifications=[list(item) for item in cfg.desert_classifications],
    )


@router.get(
    "/areas",
    response_model=List[AreaSummaryAnalyticsResponse],
    summary="List analytics summaries across all geographic areas",
)
def get_areas_analytics(
    include_breakdown: bool = Query(
        False,
        description="Whether to include full category breakdown in the response for each area",
    ),
    db: Session = Depends(get_db),
):
    """
    Calculates deterministic accessibility and gap metrics across all active geographic areas.
    """
    areas = db.query(GeographicArea).order_by(GeographicArea.id).all()
    results = []

    for area in areas:
        area_summary = default_analytics_engine.analyze_area_overall(db, area)
        if not include_breakdown:
            area_summary["category_breakdown"] = None
        results.append(area_summary)

    return results


@router.get(
    "/areas/{area_id}",
    response_model=AreaSummaryAnalyticsResponse,
    summary="Get comprehensive accessibility report for a specific area",
)
def get_area_analytics(
    area_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns the comprehensive accessibility and gap report for a specific geographic area,
    including composite scores and per-category breakdowns.
    """
    area = db.query(GeographicArea).filter(GeographicArea.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geographic area with id {area_id} not found",
        )

    return default_analytics_engine.analyze_area_overall(db, area)


@router.get(
    "/areas/{area_id}/category/{category_code}",
    response_model=CategoryAnalyticsResponse,
    summary="Get category-specific accessibility breakdown for an area",
)
def get_area_category_analytics(
    area_id: int,
    category_code: str,
    db: Session = Depends(get_db),
):
    """
    Returns in-depth deterministic analytics for a specific area and service category,
    including nearest service distance, travel time, availability, capacity, service pressure,
    transport connectivity, equity score, accessibility score, and reality gap indicators.
    """
    area = db.query(GeographicArea).filter(GeographicArea.id == area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Geographic area with id {area_id} not found",
        )

    category = (
        db.query(ServiceCategory)
        .filter(ServiceCategory.code == category_code.lower())
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service category with code '{category_code}' not found",
        )

    return default_analytics_engine.analyze_area_category(db, area, category)


@router.get(
    "/deserts",
    response_model=List[ServiceDesertItemResponse],
    summary="List all identified service deserts across areas and categories",
)
def get_service_deserts(
    category_code: Optional[str] = Query(
        None,
        description="Filter deserts by service category code (e.g. healthcare, water, electricity)",
    ),
    max_score: float = Query(
        39.9,
        description="Maximum accessibility score threshold to qualify as a desert (default <= 39.9)",
    ),
    db: Session = Depends(get_db),
):
    """
    Scans all geographic areas and service categories to identify service deserts
    (areas with Accessibility Score <= max_score, corresponding to Underserved or Critical Desert).
    """
    query = db.query(ServiceCategory).filter_by(is_active=True)
    if category_code:
        query = query.filter(ServiceCategory.code == category_code.lower())

    categories = query.all()
    areas = db.query(GeographicArea).order_by(GeographicArea.id).all()

    deserts: List[dict] = []
    for area in areas:
        for cat in categories:
            metrics = default_analytics_engine.analyze_area_category(db, area, cat)
            score = metrics["accessibility_score"]
            if score <= max_score:
                deserts.append(
                    {
                        "area_id": area.id,
                        "area_name": area.name,
                        "category_code": cat.code,
                        "category_name": cat.name,
                        "accessibility_score": score,
                        "gap_score": metrics["gap_score"],
                        "service_desert_classification": metrics["service_desert_classification"],
                        "nearest_service_name": metrics["nearest_service_name"],
                        "distance_km": metrics["distance_km"],
                        "pressure_category": metrics["service_pressure"]["pressure_category"],
                    }
                )

    # Sort deserts by severity (lowest accessibility score first)
    deserts.sort(key=lambda d: d["accessibility_score"])
    return deserts


@router.get(
    "/rankings/underserved",
    response_model=UnderservedRankingsResponse,
    summary="Get ranked leaderboard of most underserved civic areas",
)
def get_underserved_rankings(
    category_code: Optional[str] = Query(
        None,
        description="Filter ranking by specific service category (e.g. healthcare, education), or omit for composite ranking",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of ranked areas to return (default 10)",
    ),
    min_gap: float = Query(
        0.0,
        ge=0.0,
        le=100.0,
        description="Minimum gap score threshold to be included in ranking (default 0.0)",
    ),
    db: Session = Depends(get_db),
):
    """
    Ranks civic areas from most underserved to least underserved using existing Stage 3 analytics.
    Powers the Core Dashboard's Top Underserved Localities widget and Map prioritization filters.
    """
    areas = db.query(GeographicArea).order_by(GeographicArea.id).all()
    candidates_ranked = []

    if category_code:
        cat_obj = (
            db.query(ServiceCategory)
            .filter(ServiceCategory.code == category_code.lower())
            .first()
        )
        if not cat_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service category with code '{category_code}' not found",
            )

        eval_label = cat_obj.code
        for a in areas:
            metrics = default_analytics_engine.analyze_area_category(db, a, cat_obj)
            gap = float(metrics["gap_score"])
            if gap >= min_gap:
                candidates_ranked.append(
                    {
                        "area_id": a.id,
                        "area_name": a.name,
                        "area_type": a.area_type,
                        "population": int(a.population),
                        "accessibility_score": float(metrics["accessibility_score"]),
                        "gap_score": gap,
                        "desert_classification": metrics["service_desert_classification"],
                        "category_evaluated": cat_obj.code,
                        "most_critical_category": cat_obj.code,
                        "nearest_service_name": metrics.get("nearest_service_name"),
                        "service_pressure_category": metrics.get("service_pressure", {}).get("pressure_category"),
                        "confidence_score": float(metrics.get("confidence_score", 1.0)),
                    }
                )
    else:
        eval_label = "composite"
        for a in areas:
            summary = default_analytics_engine.analyze_area_overall(db, a)
            gap = float(summary["composite_gap_score"])
            if gap >= min_gap:
                breakdown = summary.get("category_breakdown") or []
                worst_cat = None
                worst_cat_gap = -1.0
                for item in breakdown:
                    if item["gap_score"] > worst_cat_gap:
                        worst_cat_gap = item["gap_score"]
                        worst_cat = item["category_code"]

                candidates_ranked.append(
                    {
                        "area_id": a.id,
                        "area_name": a.name,
                        "area_type": a.area_type,
                        "population": int(a.population),
                        "accessibility_score": float(summary["composite_accessibility_score"]),
                        "gap_score": gap,
                        "desert_classification": summary["composite_desert_classification"],
                        "category_evaluated": "composite",
                        "most_critical_category": worst_cat,
                        "nearest_service_name": None,
                        "service_pressure_category": None,
                        "confidence_score": 1.0,
                    }
                )

    # Deterministic sorting: primary = gap_score descending, secondary = population descending, tertiary = area_id ascending
    candidates_ranked.sort(key=lambda x: (-x["gap_score"], -x["population"], x["area_id"]))

    # Apply limit
    limited_candidates = candidates_ranked[:limit]

    # Assign sequential ranks 1, 2, 3...
    ranking_items = []
    underserved_count = 0
    for idx, item in enumerate(limited_candidates, start=1):
        if item["desert_classification"] in ["Critical Desert", "Underserved", "At Risk"]:
            underserved_count += 1
        ranking_items.append(
            UnderservedAreaRankingItem(
                rank=idx,
                area_id=item["area_id"],
                area_name=item["area_name"],
                area_type=item["area_type"],
                population=item["population"],
                accessibility_score=item["accessibility_score"],
                gap_score=item["gap_score"],
                desert_classification=item["desert_classification"],
                category_evaluated=item["category_evaluated"],
                most_critical_category=item["most_critical_category"],
                nearest_service_name=item["nearest_service_name"],
                service_pressure_category=item["service_pressure_category"],
                confidence_score=item["confidence_score"],
            )
        )

    return UnderservedRankingsResponse(
        category_evaluated=eval_label,
        total_areas_evaluated=len(areas),
        underserved_areas_count=underserved_count,
        rankings=ranking_items,
    )
