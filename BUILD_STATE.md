# CivicPulse Build State Tracking

## Current Status
- **Current Stage**: Stage 4B (Recommendation Scoring Engine)
- **Status**: PASS
- **Next Stage**: Stage 4C

---

## Stage History

### Stage 0: Project Foundation
- **Result**: PASS
- **Files Changed**:
  - `.gitignore`, `.env.example`, `docker-compose.yml`, `API_CONTRACT.md`, `README.md`, `BUILD_STATE.md`, `docs/checkpoints/STAGE-00.md`
  - `backend/.env.example`, `backend/.env`, `backend/Dockerfile`, `backend/requirements.txt`, `backend/run.py`, `backend/start_db.py`
  - `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/database.py`, `backend/app/main.py`
  - `backend/tests/__init__.py`, `backend/tests/test_health.py`
  - `frontend/*` (Vite + React scaffold - Person 1)

---

### Stage 1: Database + Demo Data
- **Result**: PASS
- **Database Architecture**:
  - Relational & Geospatial engine supporting PostgreSQL/PostGIS (production/container) and SQLite with Shapely (local dev).
  - Spatial custom decorator `SafeGeometry` managing SRID 4326 geometries (Point, Polygon, MultiPolygon).
  - Multi-scale hierarchy support: City -> Ward/District -> Neighbourhood.
- **Tables Created**:
  - `data_sources`, `service_categories`, `geographic_areas`, `population_cells`, `services`, `service_capacities`, `community_reports`, `report_verifications`, `audit_logs`

---

### Stage 2: Backend Core + Auth
- **Result**: PASS

- **Auth Architecture**:
  - Stateless JSON Web Tokens (JWT) signed via HS256 algorithm with configurable secret key and expiration.
  - Salted password hashing with `bcrypt` (12 rounds) guaranteeing zero plain-text credential persistence.
  - OAuth2 Password Bearer authentication scheme with `/auth/login` token endpoint.
  - Server-side token validation extracting user identity and authorization claims directly from database sessions.
  - Reusable FastAPI route dependencies: `get_current_user`, `require_active_user`, `require_role`, `require_permission`.

- **Role Architecture (RBAC)**:
  - `Role` model with Many-to-Many relationship to `Permission` via `role_permissions`.
  - Four discrete system roles:
    1. `citizen`: Public read access (`data:read`), civic report submission (`report:create`).
    2. `community`: Citizen capabilities + peer community verification (`report:verify_community`).
    3. `authority`: Municipal operations (`authority:operate`), official audit verification (`report:verify_official`).
    4. `admin`: Full administrative control (`admin:manage`) and system oversight.

- **Authentication Commands**:
  - Login via API: `POST /auth/login` with JSON `{"email": "...", "password": "..."}`
  - Check current identity: `GET /auth/me` with header `Authorization: Bearer <token>`
  - Role verification tests: `GET /auth/verify-role/{authority|admin|community}`

- **Demo Accounts**:
  - `citizen@example.com` / `Citizen123!` (Role: `citizen`)
  - `community@example.com` / `Community123!` (Role: `community`)
  - `authority@example.com` / `Authority123!` (Role: `authority`)
  - `admin@example.com` / `Admin123!` (Role: `admin`)
  - `inactive@example.com` / `Inactive123!` (Role: `citizen`, Inactive - 403 test)

- **Commands that Work**:
  - Migrations: `backend\.venv\Scripts\alembic.exe upgrade head`
  - Seeding: `backend\.venv\Scripts\python.exe backend\seed.py`
  - Test Suite: `backend\.venv\Scripts\pytest.exe backend\tests` (60/60 passing)
  - Backend Runner: `backend\.venv\Scripts\python.exe backend\run.py`

- **Known Issues**:
  - None. Server-side RBAC and token validation fully operational.

---

### Stage 3: Geospatial / Analytics Engine
- **Result**: PASS

- **Analytics Architecture**:
  - Backend-owned deterministic civic calculation engine converting spatial, service, demand, capacity, and transport data into multi-dimensional accessibility metrics.
  - Centralized, validated `AnalyticsConfig` governing:
    - 30% Travel Time Score
    - 20% Service Availability Score
    - 20% Capacity Score
    - 15% Transport Connectivity Score
    - 15% Equity Score
  - Deterministic distance via Haversine great-circle calculation and centroid extraction (WKT and GeoJSON).
  - Pluggable `RoutingProvider` abstraction with `DeterministicRoutingProvider` using configurable transit and walking speed approximations.
  - Operational availability scoring:
    - `operational`: 100, `limited`: 60, `degraded`: 50, `temporarily_unavailable`: 20, `closed`: 0
  - Service pressure calculation (`Demand / Available Capacity`) with categorical classification:
    - `Low`, `Moderate`, `High`, `Critical`
    - Graceful zero and missing capacity handling without division by zero.
  - Baseline service desert classifications:
    - 80–100: Well Served
    - 60–79: Adequate
    - 40–59: At Risk
    - 20–39: Underserved
    - 0–19: Critical Desert
  - Deterministic Gap Score:
    - `Gap Score = 100 - Accessibility Score` (guaranteed `0 <= Gap Score <= 100`)
  - Ground truth integration calculating **Confidence Score** and **Reality Gap** from active citizen and community reports.

- **Endpoints Created**:
  - `GET /analytics/config`
  - `GET /analytics/areas`
  - `GET /analytics/areas/{area_id}`
  - `GET /analytics/areas/{area_id}/category/{category_code}`
  - `GET /analytics/deserts`

---

### Stage 4A: Candidate Location Engine
- **Result**: PASS

- **Candidate Generation Architecture**:
  - Backend service `CandidateLocationService` identifying candidate infrastructure placement locations for `healthcare`, `education`, `transport`, `water`, and `market`.
  - Multi-strategy candidate derivation:
    - `centroid`: Interior centroid or representative point of the underserved locality.
    - `population_node`: Highest-density demand center derived from population cell geometries or community clusters.
    - `gap_perimeter`: Coverage gap point maximizing geographic distance from existing facilities to eliminate dead zones.
  - Underserved area filtering:
    - Excludes areas with sufficient access (`Well Served`, accessibility $\ge 80\%$).
    - Ranks qualifying areas by gap score descending.
  - Spatial and geographic validation:
    - Validates coordinate bounds (`[-90, 90]`, `[-180, 180]`), finiteness (non-NaN/inf).
    - Validates Shapely geometric topology and polygon boundary containment with buffer tolerance.
    - Fault-tolerant rejection handling: invalid coordinates or broken geometries are flagged as `rejected` with reasons without terminating the batch.
  - Spatial deduplication:
    - Suppresses duplicate or overlapping candidate points within 0.0001 degrees (~11 meters).
  - Determinism:
    - Guarantee 100% deterministic output order sorted by `(area_id, strategy, candidate_id)`.

- **Endpoints Created**:
  - `GET /decision/candidates`
  - `POST /decision/candidates/generate`

- **Files Changed**:
  - `backend/app/decision/__init__.py`
  - `backend/app/decision/candidates.py`
  - `backend/app/schemas/decision.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/decision.py`
  - `backend/app/routes/__init__.py`
  - `backend/app/main.py`
  - `backend/tests/test_candidates.py`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-04A.md`

- **Checks Run**:
  - Candidate generation: PASS
  - Invalid geometry handling: PASS
  - Invalid coordinate handling: PASS
  - Unsupported service handling: PASS
  - Deterministic output: PASS
  - Duplicate prevention: PASS
  - Backend startup / OpenAPI: PASS
  - Full test suite: PASS (45/45 passing)

- **Next Stage**:
  - Stage 4B

---

### Stage 4B: Recommendation Scoring Engine
- **Result**: PASS

- **Recommendation Formula**:
  - `Recommendation Score = (0.30 × Gap) + (0.25 × Population) + (0.15 × Travel Need) + (0.10 × Capacity Pressure) + (0.10 × Equity Need) + (0.05 × Connectivity) + (0.05 × Data Confidence)`
  - Normalized strictly within 0.0 to 100.0.

- **Factor Weights**:
  - Gap Severity: 30%
  - Population Affected: 25%
  - Travel-Time Need: 15%
  - Capacity Pressure: 10%
  - Equity Need: 10%
  - Connectivity: 5%
  - Data Confidence: 5%
  - Validated using Pydantic `RecommendationConfig` (weights sum strictly to 1.0).

- **Normalization Method**:
  - Gap: Clamped 0–100 deficit score.
  - Population: Scaled against reference population (default 25,000 residents).
  - Travel-Time Need: Inverse travel-time score (`100.0 - travel_time_score`), unreached = 100.0.
  - Capacity Pressure: Service load mapping (`Critical` = 100, `High` = 75, `Moderate` = 50, `Low` = 20).
  - Equity Need: Demographic vulnerability index (0–100).
  - Connectivity: Transit accessibility index (0–100).
  - Data Confidence: Telemetry/report agreement index (0–100).

- **Ranking & Tie-Breaking Method**:
  - Primary Sort: `recommendation_score` descending.
  - Secondary Sort (Tie-breaker 1): `population` descending.
  - Tertiary Sort (Tie-breaker 2): `candidate_id` ascending.
  - Sequential ranks `1, 2, 3...` assigned.
  - Invalid candidates excluded with recorded rejection reasons.

- **API Endpoints**:
  - `POST /recommendations`
  - `GET /recommendations`

- **Files Changed**:
  - `backend/app/decision/recommendation.py`
  - `backend/app/decision/__init__.py`
  - `backend/app/schemas/recommendation.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/recommendations.py`
  - `backend/app/routes/__init__.py`
  - `backend/app/main.py`
  - `backend/tests/test_recommendations.py`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-04B.md`

- **Checks Run**:
  - Recommendation score calculation: PASS
  - Weight validation: PASS
  - Normalization: PASS
  - Score range (0–100): PASS
  - Ranking: PASS
  - Tie-breaking: PASS
  - Invalid candidates exclusion: PASS
  - Missing data handling: PASS
  - Explanation fields: PASS
  - Service-type validation: PASS
  - Stage 3 regression tests: PASS (14/14)
  - Stage 4A regression tests: PASS (13/13)
  - Backend startup / OpenAPI: PASS (15 endpoints)
  - Seeded demo ranking: PASS (60/60 passing)

- **Known Limitations**:
  - Does not execute post-intervention simulation or budget optimization. Those belong to Stage 4C and Stage 5.

- **Next Stage**:
  - Stage 4C
