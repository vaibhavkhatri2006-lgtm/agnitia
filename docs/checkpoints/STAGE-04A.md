# Stage 04A Checkpoint

## Objective
Establish the candidate location engine for CivicPulse as Person 2 (Backend / GIS / Analytics). The engine identifies, derives, and validates deterministic candidate locations where new civic facilities could be situated to resolve service deserts and accessibility gaps, without making final recommendation decisions or ranking optimizations.

---

## Implemented
1. **Candidate Location Domain & Service Layer (`app.decision.candidates`)**:
   - `CandidateLocation` data model tracking all required candidate attributes.
   - `CandidateLocationService` managing candidate generation, validation, and deduplication.
   - Supported service validation covering `healthcare`, `education`, `transport`, `water`, and `market`.
2. **Geospatial & Containment Validation**:
   - Coordinate boundary and finiteness verification (`-90 <= lat <= 90`, `-180 <= lon <= 180`, non-NaN/inf).
   - Shapely geometric topology validity verification.
   - Area polygon boundary containment verification using WKT MultiPolygon parsing with buffer tolerance.
   - Fault-tolerant error recording: invalid points are flagged with `validity_status="rejected"` without halting the candidate generation batch.
3. **Deterministic Multi-Strategy Candidate Generation**:
   - **Strategy 1 (`centroid`)**: Geometric interior center / representative point of underserved area polygon.
   - **Strategy 2 (`population_node`)**: High-demand population center derived from population cell geometries or community demand nodes.
   - **Strategy 3 (`gap_perimeter`)**: Strategic coverage point maximizing geographic distance from existing facilities to eliminate service dead zones.
   - Duplicate prevention within 0.0001 degrees (~11 meters) tolerance.
   - Deterministic sort ordering by `(area_id, strategy, candidate_id)`.
4. **Pydantic Schemas & API Endpoints (`app.routes.decision`, `app.schemas.decision`)**:
   - `CandidateLocationResponse`: Full schema including scores, population, gap, nearby facilities, and validity.
   - `GET /decision/candidates`: Query endpoint with `service_type`, `min_gap_threshold`, and `max_accessibility`.
   - `POST /decision/candidates/generate`: JSON payload generation endpoint.
   - OpenAPI tag and schema registration in FastAPI application.
5. **Comprehensive Automated Test Suite (`tests/test_candidates.py`)**:
   - 13 dedicated unit, integration, and API tests validating all 8 requirements.

---

## Candidate Strategy Details
- **Filtering Underserved Areas**: Excludes areas classified as "Well Served" or with accessibility $\ge 80\%$.
- **Prioritization**: Ranks areas by gap score descending, ensuring the most severe service deserts (e.g. Highlands Valley for healthcare with Gap $86.9\%$) generate candidate options first.
- **Coordinates Integrity**: Coordinates are strictly evaluated for polygon containment inside the assigned locality before being stamped as `valid`.

---

## Files Changed
- `backend/app/decision/__init__.py` (New): Package exports for candidate service.
- `backend/app/decision/candidates.py` (New): `CandidateLocationService` and `CandidateLocation` implementation.
- `backend/app/schemas/decision.py` (New): Pydantic request/response schemas.
- `backend/app/schemas/__init__.py` (Modified): Exported decision schemas.
- `backend/app/routes/decision.py` (New): FastAPI candidate endpoints.
- `backend/app/routes/__init__.py` (Modified): Exported `decision_router`.
- `backend/app/main.py` (Modified): Registered `decision_router` and OpenAPI tag.
- `backend/tests/test_candidates.py` (New): 13 focused test cases for Stage 4A.
- `API_CONTRACT.md` (Modified): Documented version 0.4.0 and Section 4 candidate endpoints.
- `BUILD_STATE.md` (Modified): Set Stage 4A = PASS, next = Stage 4B.
- `docs/checkpoints/STAGE-04A.md` (New): Checkpoint record.

---

## Checks Run
- **Candidate generation tests**: PASS (Valid candidates generated with all required fields).
- **Invalid geometry test**: PASS (Corrupt geometry safely parsed and rejected without batch crash).
- **Invalid coordinate test**: PASS (NaN, out-of-bounds, non-numeric correctly flagged).
- **Unsupported service test**: PASS (Descriptive 400 Bad Request error returned).
- **Deterministic output test**: PASS (Identical output across multiple consecutive runs).
- **Duplicate candidate test**: PASS (Duplicates prevented within spatial tolerance).
- **Backend startup / OpenAPI check**: PASS (14 endpoints active, valid OpenAPI 3.1.0 schema).
- **Stage 3 analytics tests**: PASS (All 14 analytics tests remain passing).
- **Full test suite**: PASS (45 passed, 0 failed across all stages).

---

## Result
**PASS**

---

## Known Issues
None.

---

## Next Stage
**STAGE 4B — RECOMMENDATION & IMPACT ENGINE**
