"""
Schemas for Community Reports, Civic Trust, and Verification Workflows.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    """Payload for submitting a community service report."""
    title: str = Field(..., min_length=3, max_length=200, description="Brief report summary")
    description: str = Field(..., min_length=5, description="Detailed observation or issue description")
    category_code: Optional[str] = Field(None, description="Category code (e.g. healthcare, water, transport)")
    category_id: Optional[int] = Field(None, description="Category database ID")
    service_id: Optional[int] = Field(None, description="Target civic facility ID if applicable")
    area_id: Optional[int] = Field(None, description="Geographic area ID")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    severity: str = Field("medium", description="Issue severity: low, medium, high, critical")
    evidence_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata (photo URLs, telemetry, sensor readings)")


class ReportVerificationRequest(BaseModel):
    """Payload for reviewing and verifying a community report."""
    verification_status: str = Field(
        ...,
        description="Target status: COMMUNITY_VERIFIED, AUTHORITY_VERIFIED, OFFICIAL, REJECTED",
    )
    notes: Optional[str] = Field(None, description="Verification reason, field observations, or audit notes")


class ReportVerificationItem(BaseModel):
    """Historical verification event."""
    id: int
    verifier_id: Optional[str]
    verification_status: str
    verification_type: str
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogItem(BaseModel):
    """Audit log entry tracking report status mutations."""
    id: int
    actor_id: Optional[str]
    action: str
    entity_type: str
    entity_id: int
    previous_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """Representation of a community report."""
    id: int
    reporter_id: Optional[str]
    category_id: Optional[int]
    category_code: Optional[str]
    service_id: Optional[int]
    service_name: Optional[str]
    area_id: Optional[int]
    area_name: Optional[str]
    title: str
    description: str
    latitude: float
    longitude: float
    severity: str
    status: str
    verification_status: str
    confidence_score: float
    source_type: str
    created_at: datetime
    updated_at: datetime
    evidence_metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ReportDetailResponse(ReportResponse):
    """Detailed report representation with verification log and audit history."""
    verifications: List[ReportVerificationItem] = Field(default_factory=list)
    audit_trail: List[AuditLogItem] = Field(default_factory=list)
