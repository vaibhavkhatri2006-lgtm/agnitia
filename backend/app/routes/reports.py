"""
Routes for Community Reports, Verification Workflows, and Civic Trust.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from shapely.geometry import Point
from shapely import wkt

from app.database import get_db
from app.dependencies.auth import require_active_user
from app.models.user import User
from app.models.community_report import CommunityReport
from app.models.report_verification import ReportVerification
from app.models.audit_log import AuditLog
from app.models.service_category import ServiceCategory
from app.models.service import Service
from app.models.geographic_area import GeographicArea
from app.schemas.reports import (
    ReportCreateRequest,
    ReportVerificationRequest,
    ReportVerificationItem,
    AuditLogItem,
    ReportResponse,
    ReportDetailResponse,
)

router = APIRouter(prefix="/reports", tags=["Community Reports & Trust"])


def calculate_confidence_score(
    verification_status: str,
    verifications_count: int = 1,
    has_evidence: bool = False,
    is_recent: bool = True,
) -> float:
    """
    Calculates a simple transparent confidence/trust score based on:
    - verification status (PENDING_REVIEW, COMMUNITY_VERIFIED, AUTHORITY_VERIFIED, OFFICIAL, REJECTED)
    - number of supporting verifications / evidence
    - recency
    """
    status_upper = verification_status.strip().upper()
    if status_upper == "REJECTED":
        return 0.0
    if status_upper == "OFFICIAL":
        return 1.00
    if status_upper == "AUTHORITY_VERIFIED":
        return 0.95
    if status_upper == "COMMUNITY_VERIFIED":
        support_bonus = min(0.15, max(0, verifications_count - 1) * 0.05)
        evidence_bonus = 0.05 if has_evidence else 0.0
        return min(0.90, round(0.75 + support_bonus + evidence_bonus, 2))
    
    # PENDING_REVIEW or SUBMITTED
    evidence_bonus = 0.05 if has_evidence else 0.0
    return min(0.60, round(0.50 + evidence_bonus, 2))


def report_to_response(
    r: CommunityReport,
    evidence_metadata: Optional[Dict[str, Any]] = None,
) -> ReportResponse:
    """Converts a CommunityReport ORM instance into a ReportResponse schema."""
    return ReportResponse(
        id=r.id,
        reporter_id=r.reporter_id,
        category_id=r.category_id,
        category_code=r.category.code if r.category else None,
        service_id=r.service_id,
        service_name=r.service.name if r.service else None,
        area_id=r.area_id,
        area_name=r.area.name if r.area else None,
        title=r.title,
        description=r.description,
        latitude=float(r.latitude),
        longitude=float(r.longitude),
        severity=r.severity,
        status=r.status,
        verification_status=r.verification_status,
        confidence_score=float(r.confidence_score),
        source_type=r.source_type,
        created_at=r.created_at,
        updated_at=r.updated_at,
        evidence_metadata=evidence_metadata,
    )


def report_to_detail_response(
    r: CommunityReport,
    db: Session,
    evidence_metadata: Optional[Dict[str, Any]] = None,
) -> ReportDetailResponse:
    """Converts a CommunityReport ORM instance into a ReportDetailResponse schema with history."""
    verifications = [
        ReportVerificationItem(
            id=v.id,
            verifier_id=v.verifier_id,
            verification_status=v.verification_status,
            verification_type=v.verification_type,
            notes=v.notes,
            created_at=v.created_at,
        )
        for v in (r.verifications or [])
    ]

    audit_records = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "community_report", AuditLog.entity_id == r.id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    audit_trail = [
        AuditLogItem(
            id=a.id,
            actor_id=a.actor_id,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            previous_value=a.previous_value,
            new_value=a.new_value,
            reason=a.reason,
            created_at=a.created_at,
        )
        for a in audit_records
    ]

    base = report_to_response(r, evidence_metadata=evidence_metadata)
    return ReportDetailResponse(
        **base.model_dump(),
        verifications=verifications,
        audit_trail=audit_trail,
    )


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a community service report",
)
def create_report(
    req: ReportCreateRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """
    Submits a community-generated infrastructure or service report.
    Any active user (citizen, community, authority, admin) can submit reports.
    Initial status is set to PENDING_REVIEW, and an audit trail log is created.
    """
    # 1. Resolve Category
    category_id = req.category_id
    if req.category_code:
        cat = db.query(ServiceCategory).filter(ServiceCategory.code == req.category_code.lower()).first()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service category with code '{req.category_code}' was not found.",
            )
        category_id = cat.id
    elif category_id:
        cat = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service category with ID {category_id} was not found.",
            )

    # 2. Resolve Service if specified
    if req.service_id:
        srv = db.query(Service).filter(Service.id == req.service_id).first()
        if not srv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Civic service facility with ID {req.service_id} was not found.",
            )
        if not category_id:
            category_id = srv.category_id

    # 3. Resolve Area
    area_id = req.area_id
    if not area_id:
        # Spatial containment lookup for convenience
        pt = Point(req.longitude, req.latitude)
        areas = db.query(GeographicArea).all()
        for a in areas:
            if a.geometry:
                try:
                    poly = wkt.loads(a.geometry)
                    if poly.contains(pt):
                        area_id = a.id
                        break
                except Exception:
                    pass

    # 4. Confidence & Initial Status
    confidence = calculate_confidence_score(
        "PENDING_REVIEW",
        verifications_count=1,
        has_evidence=bool(req.evidence_metadata),
        is_recent=True,
    )

    report = CommunityReport(
        reporter_id=str(current_user.id),
        category_id=category_id,
        service_id=req.service_id,
        area_id=area_id,
        title=req.title,
        description=req.description,
        latitude=req.latitude,
        longitude=req.longitude,
        geometry=f"POINT({req.longitude} {req.latitude})",
        severity=req.severity.lower(),
        status="PENDING_REVIEW",
        source_type="community",
        verification_status="PENDING_REVIEW",
        confidence_score=confidence,
    )
    db.add(report)
    db.flush()

    # 5. Audit Log (SUBMITTED -> PENDING_REVIEW)
    audit_entry = AuditLog(
        actor_id=str(current_user.id),
        action="create",
        entity_type="community_report",
        entity_id=report.id,
        previous_value="SUBMITTED",
        new_value="PENDING_REVIEW",
        reason=f"Initial community report submitted: {report.title}",
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(report)

    return report_to_response(report, evidence_metadata=req.evidence_metadata)


@router.get(
    "",
    response_model=List[ReportResponse],
    summary="List community reports with optional filtering",
)
def list_reports(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    category_code: Optional[str] = Query(None, description="Filter by category code"),
    area_id: Optional[int] = Query(None, description="Filter by geographic area ID"),
    service_id: Optional[int] = Query(None, description="Filter by civic facility ID"),
    limit: int = Query(50, ge=1, le=200, description="Max reports to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
):
    """Retrieves community reports cataloged in the system with optional filters."""
    query = db.query(CommunityReport)

    if status_filter:
        query = query.filter(CommunityReport.status == status_filter.strip().upper())
    if verification_status:
        query = query.filter(CommunityReport.verification_status == verification_status.strip().upper())
    if category_code:
        query = query.join(ServiceCategory).filter(ServiceCategory.code == category_code.lower())
    if area_id is not None:
        query = query.filter(CommunityReport.area_id == area_id)
    if service_id is not None:
        query = query.filter(CommunityReport.service_id == service_id)

    reports = query.order_by(CommunityReport.id.desc()).offset(offset).limit(limit).all()
    return [report_to_response(r) for r in reports]


@router.get(
    "/{report_id}",
    response_model=ReportDetailResponse,
    summary="Get report details with verification history and audit log",
)
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves an individual report by ID with full verification events and audit history."""
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community report with ID {report_id} was not found.",
        )
    return report_to_detail_response(report, db)


@router.post(
    "/{report_id}/verify",
    response_model=ReportDetailResponse,
    summary="Verify or moderate a community report",
)
def verify_report(
    report_id: int,
    req: ReportVerificationRequest,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """
    Executes the verification and moderation workflow for a community report.
    Enforces server-side RBAC:
    - Citizen: Cannot verify or approve reports (403 Forbidden).
    - Community: Can submit COMMUNITY_VERIFIED.
    - Authority: Can approve AUTHORITY_VERIFIED, OFFICIAL, or REJECTED.
    - Admin: Full moderation permissions across all states.
    """
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community report with ID {report_id} was not found.",
        )

    target_status = req.verification_status.strip().upper()
    valid_statuses = {"COMMUNITY_VERIFIED", "AUTHORITY_VERIFIED", "OFFICIAL", "REJECTED"}
    if target_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid target verification status '{target_status}'. Must be one of: {', '.join(sorted(valid_statuses))}",
        )

    user_role = current_user.role_name.lower()

    # Enforce RBAC server-side
    if target_status == "COMMUNITY_VERIFIED":
        if user_role not in ["community", "authority", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user_role}' cannot perform community verification. Requires community, authority, or admin.",
            )
        verification_type = "peer_confirmation" if user_role == "community" else "official_audit"

    elif target_status in ["AUTHORITY_VERIFIED", "OFFICIAL"]:
        if user_role not in ["authority", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user_role}' cannot approve '{target_status}'. Authority or admin role required.",
            )
        verification_type = "official_audit" if user_role == "authority" else "admin_moderation"

    elif target_status == "REJECTED":
        if user_role not in ["authority", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user_role}' cannot reject reports. Authority or admin role required.",
            )
        verification_type = "official_audit" if user_role == "authority" else "admin_moderation"

    old_status = report.verification_status

    # 1. Record Verification Event
    verification_entry = ReportVerification(
        report_id=report.id,
        verifier_id=str(current_user.id),
        verification_status=target_status,
        verification_type=verification_type,
        notes=req.notes,
    )
    db.add(verification_entry)
    db.flush()

    # 2. Record Audit Log Entry
    audit_entry = AuditLog(
        actor_id=str(current_user.id),
        action="status_change",
        entity_type="community_report",
        entity_id=report.id,
        previous_value=old_status,
        new_value=target_status,
        reason=req.notes or f"Report verified as {target_status} by {user_role}",
    )
    db.add(audit_entry)

    # 3. Recalculate Confidence Score
    verifications_count = db.query(ReportVerification).filter(ReportVerification.report_id == report.id).count()
    new_confidence = calculate_confidence_score(
        target_status,
        verifications_count=verifications_count,
        has_evidence=False,
        is_recent=True,
    )

    report.verification_status = target_status
    report.status = target_status
    report.confidence_score = new_confidence
    db.commit()
    db.refresh(report)

    return report_to_detail_response(report, db)


@router.get(
    "/{report_id}/audit-trail",
    response_model=List[AuditLogItem],
    summary="Get audit log trail for a report",
)
def get_report_audit_trail(
    report_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves all immutable audit log records associated with a specific report."""
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community report with ID {report_id} was not found.",
        )

    audit_records = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "community_report", AuditLog.entity_id == report_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    return [
        AuditLogItem(
            id=a.id,
            actor_id=a.actor_id,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            previous_value=a.previous_value,
            new_value=a.new_value,
            reason=a.reason,
            created_at=a.created_at,
        )
        for a in audit_records
    ]
