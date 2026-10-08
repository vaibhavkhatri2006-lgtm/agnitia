# Stage 7 Checkpoint — Community + Civic Trust

## Objective
Implement the backend workflow for community-submitted service reports, multi-tier verification with server-side Role-Based Access Control (RBAC), transparent confidence/trust scoring, and an immutable audit log trail.

---

## Implemented

1. **Community Report Creation (`POST /reports`)**:
   - Allows citizens and authenticated users to submit service reports.
   - Captures title, description, category/service references, geographic coordinates (lat/lng), severity level (`low`, `medium`, `high`, `critical`), and optional evidence metadata (photos, telemetry).
   - Establishes initial status: `SUBMITTED` → `PENDING_REVIEW`.
   - Dynamic containment lookup assigns `area_id` based on reported coordinates if not specified.
   - Automatically logs initial audit trail event (`SUBMITTED` -> `PENDING_REVIEW`).

2. **Verification & Moderation Workflow (`POST /reports/{report_id}/verify`)**:
   - Supports lifecycle progression:
     `PENDING_REVIEW` → `COMMUNITY_VERIFIED` → `AUTHORITY_VERIFIED` → `OFFICIAL`
     and `REJECTED`.
   - Strict server-side RBAC enforcement:
     - **Citizen**: Can create reports; forbidden (`403`) from authority-verifying, community-verifying, or approving official status.
     - **Community**: Can verify reports as `COMMUNITY_VERIFIED` (`peer_confirmation`); forbidden (`403`) from approving official status.
     - **Authority**: Can verify reports as `AUTHORITY_VERIFIED`, promote to `OFFICIAL` (`official_audit`), and reject reports (`REJECTED`).
     - **Admin**: Full moderation across all states and rejection.

3. **Transparent Confidence / Trust Scoring**:
   - Deterministic and explainable scoring model:
     - `REJECTED`: `0.00`
     - `PENDING_REVIEW`: `0.50` (or `0.55` with evidence metadata)
     - `COMMUNITY_VERIFIED`: `0.75` base + `0.05` per additional supporting verification (capped at `0.90`)
     - `AUTHORITY_VERIFIED`: `0.95`
     - `OFFICIAL`: `1.00`

4. **Immutable Audit Trail (`GET /reports/{report_id}/audit-trail`)**:
   - Every status mutation creates an audit record capturing:
     - `actor_id`: ID of the user performing the change
     - `action`: `create` or `status_change`
     - `entity_type`: `community_report`
     - `entity_id`: ID of the target report
     - `previous_value`: Previous status (e.g. `PENDING_REVIEW`)
     - `new_value`: New status (e.g. `COMMUNITY_VERIFIED`)
     - `reason`: Verification notes or system explanation
     - `created_at`: Immutable UTC timestamp

5. **List & Detail Endpoints**:
   - `GET /reports`: Lists reports with filtering by status, verification status, category, area, and service.
   - `GET /reports/{report_id}`: Returns complete report details including all verifications and audit log history.

---

## Checks

- Citizen report creation: **PASS**
- Citizen restriction (returns 403 on official/authority verify): **PASS**
- Community verification (`COMMUNITY_VERIFIED`): **PASS**
- Authority verification & official approval (`OFFICIAL`, confidence = 1.0): **PASS**
- Rejected workflow (`REJECTED`, confidence = 0.0): **PASS**
- Audit log tracking for status changes: **PASS**
- Existing related regression tests (`test_auth.py`): **PASS**

---

## Result
**PASS**

---

## Known Issues
- Direct binary photo uploads are represented via URLs and telemetry payloads within `evidence_metadata`. Cloud object storage (S3/GCS) signed URLs can be integrated in later phases if required.

---

## Next Stage
**STAGE 8**
