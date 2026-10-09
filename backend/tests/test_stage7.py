"""
CivicPulse Stage 7 — Community Reports, Civic Trust & Verification Workflow Tests.
Validates:
1. Citizen can create report (status = PENDING_REVIEW, initial audit entry recorded)
2. Citizen cannot authority-verify (returns 403)
3. Community verifier can community-verify (status = COMMUNITY_VERIFIED)
4. Authority can official-verify (status = OFFICIAL, confidence = 1.0)
5. Rejected workflow works (status = REJECTED, confidence = 0.0)
6. Audit record created for status changes with complete actor, action, previous/new status, reason
7. Complete end-to-end lifecycle and RBAC restrictions
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_auth_token(email: str, password: str) -> str:
    """Helper to authenticate and obtain bearer access token."""
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Authentication failed for {email}: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def citizen_token():
    return get_auth_token("citizen@example.com", "Citizen123!")


@pytest.fixture(scope="module")
def community_token():
    return get_auth_token("community@example.com", "Community123!")


@pytest.fixture(scope="module")
def authority_token():
    return get_auth_token("authority@example.com", "Authority123!")


@pytest.fixture(scope="module")
def admin_token():
    return get_auth_token("admin@example.com", "Admin123!")


def test_citizen_can_create_report(citizen_token):
    """Check 1: Citizen can create a community service report."""
    payload = {
        "title": "Severe water leakage near Central Market",
        "description": "Main pipeline broken, large pool of clean water overflowing onto roadway.",
        "category_code": "water",
        "latitude": 12.9750,
        "longitude": 77.5950,
        "severity": "high",
        "evidence_metadata": {
            "has_photo": True,
            "sensor_telemetry": {"flow_anomaly": True},
        },
    }

    response = client.post(
        "/reports",
        json=payload,
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert response.status_code == 201, f"Report creation failed: {response.text}"
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["category_code"] == "water"
    assert data["status"] == "PENDING_REVIEW"
    assert data["verification_status"] == "PENDING_REVIEW"
    assert data["confidence_score"] > 0.0
    assert data["id"] is not None


def test_citizen_cannot_authority_verify(citizen_token):
    """Check 2: Citizen cannot authority-verify or approve official status (returns 403)."""
    # Create a fresh report as citizen
    create_resp = client.post(
        "/reports",
        json={
            "title": "Pothole on 100ft road",
            "description": "Deep pothole dangerous for two-wheelers.",
            "category_code": "transport",
            "latitude": 12.9800,
            "longitude": 77.6000,
            "severity": "medium",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert create_resp.status_code == 201
    report_id = create_resp.json()["id"]

    # Citizen tries authority verification
    auth_verify_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "AUTHORITY_VERIFIED", "notes": "I approve as citizen"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert auth_verify_resp.status_code == 403, "Citizen should not be allowed to authority-verify"

    # Citizen tries official approval
    official_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "OFFICIAL", "notes": "Citizen making it official"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert official_resp.status_code == 403, "Citizen should not be allowed to approve official"

    # Citizen tries community verification
    comm_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "COMMUNITY_VERIFIED", "notes": "Citizen self-verifying"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert comm_resp.status_code == 403, "Citizen should not be allowed to verify"


def test_community_can_community_verify(citizen_token, community_token):
    """Check 3: Community member can community-verify."""
    create_resp = client.post(
        "/reports",
        json={
            "title": "Broken street lighting in ward cluster",
            "description": "Multiple streetlights off at night on 5th main.",
            "category_code": "energy" if "energy" in ["water", "healthcare"] else "water",
            "latitude": 12.9720,
            "longitude": 77.5920,
            "severity": "medium",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert create_resp.status_code == 201
    report_id = create_resp.json()["id"]

    # Community verifies
    verify_resp = client.post(
        f"/reports/{report_id}/verify",
        json={
            "verification_status": "COMMUNITY_VERIFIED",
            "notes": "Verified by community patrol group. Dark stretch confirmed.",
        },
        headers={"Authorization": f"Bearer {community_token}"},
    )
    assert verify_resp.status_code == 200, f"Community verification failed: {verify_resp.text}"
    data = verify_resp.json()
    assert data["verification_status"] == "COMMUNITY_VERIFIED"
    assert data["status"] == "COMMUNITY_VERIFIED"
    assert data["confidence_score"] >= 0.75

    # But community member cannot promote to official (403)
    official_attempt = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "OFFICIAL", "notes": "Community attempting official approval"},
        headers={"Authorization": f"Bearer {community_token}"},
    )
    assert official_attempt.status_code == 403, "Community user cannot approve official"


def test_authority_can_official_verify(citizen_token, community_token, authority_token):
    """Check 4: Authority can official-verify and approve official."""
    # 1. Citizen creates
    create_resp = client.post(
        "/reports",
        json={
            "title": "Contaminated water supply in Sector 4",
            "description": "Residents reporting turbid water with sulfur odor.",
            "category_code": "water",
            "latitude": 12.9650,
            "longitude": 77.5850,
            "severity": "critical",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert create_resp.status_code == 201
    report_id = create_resp.json()["id"]

    # 2. Community verifies
    comm_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "COMMUNITY_VERIFIED", "notes": "Multiple neighbors confirmed odor"},
        headers={"Authorization": f"Bearer {community_token}"},
    )
    assert comm_resp.status_code == 200
    assert comm_resp.json()["verification_status"] == "COMMUNITY_VERIFIED"

    # 3. Authority verifies as AUTHORITY_VERIFIED
    auth_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "AUTHORITY_VERIFIED", "notes": "Municipal water engineer dispatched"},
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert auth_resp.status_code == 200
    assert auth_resp.json()["verification_status"] == "AUTHORITY_VERIFIED"
    assert auth_resp.json()["confidence_score"] >= 0.95

    # 4. Authority marks as OFFICIAL
    official_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "OFFICIAL", "notes": "Official work order issued #WO-8821"},
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert official_resp.status_code == 200
    assert official_resp.json()["verification_status"] == "OFFICIAL"
    assert official_resp.json()["status"] == "OFFICIAL"
    assert official_resp.json()["confidence_score"] == 1.0


def test_rejected_workflow(citizen_token, authority_token):
    """Check 5: Rejected workflow works."""
    create_resp = client.post(
        "/reports",
        json={
            "title": "Spam report test",
            "description": "Invalid test issue submitted by accident.",
            "category_code": "healthcare",
            "latitude": 12.9700,
            "longitude": 77.5900,
            "severity": "low",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert create_resp.status_code == 201
    report_id = create_resp.json()["id"]

    # Authority rejects report
    reject_resp = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "REJECTED", "notes": "Dismissed as duplicate test submission."},
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert reject_resp.status_code == 200
    data = reject_resp.json()
    assert data["verification_status"] == "REJECTED"
    assert data["status"] == "REJECTED"
    assert data["confidence_score"] == 0.0


def test_audit_record_created_for_status_changes(citizen_token, community_token, authority_token):
    """Check 6: Audit record is created for every verification and status change."""
    # Create report
    create_resp = client.post(
        "/reports",
        json={
            "title": "Audit verification tracking report",
            "description": "Tracking all audit log entries during transition.",
            "category_code": "healthcare",
            "latitude": 12.9710,
            "longitude": 77.5910,
            "severity": "medium",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    report_id = create_resp.json()["id"]

    # Verify via community
    client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "COMMUNITY_VERIFIED", "notes": "Community confirmation"},
        headers={"Authorization": f"Bearer {community_token}"},
    )

    # Verify via authority
    client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "OFFICIAL", "notes": "Official municipal sign-off"},
        headers={"Authorization": f"Bearer {authority_token}"},
    )

    # Retrieve audit trail endpoint
    trail_resp = client.get(f"/reports/{report_id}/audit-trail")
    assert trail_resp.status_code == 200
    trail = trail_resp.json()

    assert len(trail) >= 3, f"Expected at least 3 audit entries, found {len(trail)}"

    # Entry 1: Creation
    assert trail[0]["action"] == "create"
    assert trail[0]["previous_value"] == "SUBMITTED"
    assert trail[0]["new_value"] == "PENDING_REVIEW"
    assert trail[0]["actor_id"] is not None

    # Entry 2: Community verify
    assert trail[1]["action"] == "status_change"
    assert trail[1]["previous_value"] == "PENDING_REVIEW"
    assert trail[1]["new_value"] == "COMMUNITY_VERIFIED"
    assert "Community confirmation" in (trail[1]["reason"] or "")

    # Entry 3: Official
    assert trail[2]["action"] == "status_change"
    assert trail[2]["previous_value"] == "COMMUNITY_VERIFIED"
    assert trail[2]["new_value"] == "OFFICIAL"
    assert "Official municipal sign-off" in (trail[2]["reason"] or "")


def test_full_lifecycle_flow(citizen_token, community_token, authority_token):
    """
    PASS CONDITION:
    Complete flow works:
    Citizen report → Review → Community verification → Authority verification → Official
    with correct RBAC and audit history.
    """
    # 1. Citizen submits report -> PENDING_REVIEW
    submit_res = client.post(
        "/reports",
        json={
            "title": "Hospital road blockage due to construction",
            "description": "Ambulances facing 20-minute delay due to unplanned trenching.",
            "category_code": "healthcare",
            "latitude": 12.9730,
            "longitude": 77.5930,
            "severity": "high",
        },
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert submit_res.status_code == 201
    report_id = submit_res.json()["id"]
    assert submit_res.json()["verification_status"] == "PENDING_REVIEW"
    assert submit_res.json()["confidence_score"] == 0.50

    # 2. Detail retrieval shows report in review
    detail_res = client.get(f"/reports/{report_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["verification_status"] == "PENDING_REVIEW"

    # 3. Community verifies -> COMMUNITY_VERIFIED
    comm_res = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "COMMUNITY_VERIFIED", "notes": "Verified by 3 area residents"},
        headers={"Authorization": f"Bearer {community_token}"},
    )
    assert comm_res.status_code == 200
    assert comm_res.json()["verification_status"] == "COMMUNITY_VERIFIED"
    assert comm_res.json()["confidence_score"] >= 0.75

    # 4. Authority verifies -> AUTHORITY_VERIFIED
    auth_res = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "AUTHORITY_VERIFIED", "notes": "Dispatched transit warden"},
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["verification_status"] == "AUTHORITY_VERIFIED"
    assert auth_res.json()["confidence_score"] >= 0.95

    # 5. Official sign-off -> OFFICIAL
    official_res = client.post(
        f"/reports/{report_id}/verify",
        json={"verification_status": "OFFICIAL", "notes": "Construction company notified and clearance ordered"},
        headers={"Authorization": f"Bearer {authority_token}"},
    )
    assert official_res.status_code == 200
    final_data = official_res.json()
    assert final_data["verification_status"] == "OFFICIAL"
    assert final_data["status"] == "OFFICIAL"
    assert final_data["confidence_score"] == 1.00

    # Verify full audit history
    assert len(final_data["verifications"]) == 3
    assert len(final_data["audit_trail"]) == 4  # 1 create + 3 status changes
