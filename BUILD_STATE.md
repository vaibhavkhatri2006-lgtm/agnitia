# CivicPulse Build State Tracking

## Current Status
- **Current Stage**: Stage 6 (Map + Core Dashboard Backend)
- **Status**: PASS
- **Map / Dashboard Backend**: Ready for Person 1 Frontend Map & Dashboard
- **Next Stage**: Stage 7

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

---

### Stage 4C: What-If / Intervention Simulation
- **Result**: PASS

- **Simulation Design**:
  - Core engine `InterventionSimulationService` in `app/decision/simulation.py`.
  - In-memory ephemeral simulation utilizing isolated `additional_services` parameter across `AnalyticsEngine`.
  - Strict safety guarantee: zero database writes, zero model insertions, zero modifications to official capacities, populations, or civic report records.
  - Multi-input support: accepts either `candidate_id` (from Stage 4A/4B) or coordinates (`latitude`, `longitude`).
  - Spatial containment resolution using Shapely geometric boundary checks to identify receiving neighbourhood.

- **Metrics Calculated**:
  - **Baseline (Before)**:
    - `accessibility_score` (population-weighted, 0–100)
    - `gap_score` (`100.0 - accessibility_score`, 0–100)
    - `service_coverage` (% population in covered areas)
    - `underserved_population` (residents living in deserts/underserved areas)
    - `average_travel_time_minutes` (population-weighted average estimated travel time)
  - **Post-Intervention (After)**:
    - Same set of 5 standardized metrics evaluated with simulated facility in-memory.
  - **Impact (Delta)**:
    - `accessibility_improvement` (+ points)
    - `gap_reduction` (- points)
    - `coverage_improvement` (+ percentage points)
    - `underserved_population_reduction` (people relieved)
    - `population_gaining_access` (people transitioning from unserved to served)
    - `travel_time_improvement_minutes` (minutes saved)
  - **Target Area Breakdown**:
    - Direct locality evaluation (e.g., Highlands Valley before: 13.1 -> after: 78.8, +65.7 pts; travel time saved: 57.9 min).
  - **Natural Language Justification & Attribution**:
    - Explanation strings with key factor identification (`travel_time_reduction`, `service_desert_resolution`, `underserved_population_relief`, `coverage_expansion`, `capacity_addition`).

- **API Endpoints**:
  - `POST /simulations`
  - `GET /simulations`

- **Files Changed**:
  - `backend/app/analytics/engine.py`
  - `backend/app/decision/simulation.py`
  - `backend/app/decision/__init__.py`
  - `backend/app/schemas/simulation.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/simulations.py`
  - `backend/app/routes/__init__.py`
  - `backend/app/main.py`
  - `backend/tests/test_simulations.py`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-04C.md`

- **Checks Run**:
  - Valid simulation: PASS
  - Invalid service type validation: PASS
  - Invalid coordinates validation: PASS
  - Invalid candidate rejection: PASS
  - Before/after calculation consistency: PASS
  - Coverage improvement: PASS (+23.9 pp in demo data)
  - Underserved population reduction: PASS (22,000 residents relieved)
  - Travel time improvement: PASS (>13 min saved citywide)
  - Deterministic results: PASS
  - Database integrity (no permanent writes): PASS
  - Explanation fields & primary factors: PASS
  - Negative/invalid impact protection: PASS
  - Scope options (city vs area): PASS
  - GET endpoint query-params: PASS
  - All 5 service types: PASS
  - Full regression test suite: PASS (76/76 passing)
  - Backend startup & OpenAPI: PASS (16 paths)

- **Known Limitations**:
  - Multi-facility combinatorial portfolio optimization and dynamic disaster cascades belong to Stage 5.

- **Next Stage**:
  - Stage 4D

---

### Stage 4D: Investment + Resilience + Future Risk (Stage 4 Complete)
- **Result**: PASS

- **Features Implemented**:
  1. **Task 1 — Investment Priority (`app.decision.investment`)**:
     - Deterministic composite score: `35% Recommendation Score + 25% Expected Impact Score + 15% Gap Severity + 15% Population Factor + 10% Equity Need`.
     - Output: Ranked interventions with strategic priority tiers (`Highest Priority`, `High Priority`, `Moderate Priority`, `Low Priority`), estimated standard cost tiers, and civic justifications.
     - Stable secondary/tertiary tie-breaking (`-investment_priority_score`, `-population`, `candidate_id`).
  2. **Task 2 — Failure / Resilience Simulation (`app.decision.resilience`)**:
     - In-memory facility outage simulation without database mutations (`excluded_service_ids`).
     - Systemic resilience score (0–100), coverage collapse percentage, newly underserved population count, directly affected population count.
     - Single point of failure detection (`Critical Infrastructure / Single Point of Failure`, `High Dependency`, `Moderate Vulnerability`, `Resilient / Redundant`).
  3. **Task 3 — Future-Risk Foundation (`app.decision.future_risk`)**:
     - Deterministic forward-looking civic risk projections under configurable population demand growth (e.g. 15% growth, 5 years).
     - Capacity saturation and headroom depletion evaluation.
     - Explicit demo labeling (`is_demo_estimate: True`, planning disclaimers).

- **Complete Decision Engine Architecture (Stage 4)**:
  - `Candidate (4A)`: Multi-strategy spatial allocation (`centroid`, `population_node`, `gap_perimeter`) with geometric boundary validation.
  - `Recommendation (4B)`: 7-factor transparent normalized scoring (0–100) with stable tie-breaking and explainable reasons.
  - `Simulation (4C)`: In-memory Before vs After what-if intervention impact measuring accessibility gains, coverage expansion, and underserved relief.
  - `Investment Priority (4D)`: Strategic capital allocation ranking balancing recommendation alignment, urgency, population scale, equity, and simulated impact return.
  - `Failure Scenario (4D)`: In-memory service outage testing identifying systemic single points of failure and network resilience.
  - `Future Risk (4D)`: Forward-looking demand growth risk foundation.

- **API Endpoints**:
  - `POST /decision/candidates/generate` & `GET /decision/candidates`
  - `POST /recommendations` & `GET /recommendations`
  - `POST /simulations` & `GET /simulations`
  - `POST /decision/investment-priorities` & `GET /decision/investment-priorities`
  - `POST /decision/failure-simulation` & `GET /decision/failure-simulation`
  - `POST /decision/future-risk` & `GET /decision/future-risk`

- **Files Changed**:
  - `backend/app/analytics/engine.py`
  - `backend/app/decision/investment.py`
  - `backend/app/decision/resilience.py`
  - `backend/app/decision/future_risk.py`
  - `backend/app/decision/__init__.py`
  - `backend/app/schemas/investment.py`
  - `backend/app/schemas/resilience.py`
  - `backend/app/schemas/future_risk.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/decision.py`
  - `backend/tests/test_stage4d.py`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-04D.md`

- **Checks Run**:
  - Investment ranking test: PASS
  - Failure simulation test: PASS
  - Future risk test: PASS
  - Deterministic output test: PASS
  - Invalid input test: PASS
  - Stage 4A regression tests: PASS (14/14)
  - Stage 4B regression tests: PASS (15/15)
  - Stage 4C regression tests: PASS (16/16)
  - Full test suite: PASS (82/82 passing)
  - Database integrity check (counts unmutated): PASS
  - Backend startup / OpenAPI: PASS (19 API paths)

- **Known Limitations**:
  - Live AI planning agents, LLM report narrative generation, and citizen reporting workflows belong to Stage 6.

- **Next Stage**:
  - Stage 5

---

### Stage 5: Frontend Integration Support
- **Result**: PASS
- **API Integration Status**: Ready for Person 1's React Frontend Connection

- **Features & Enhancements Implemented**:
  1. **CORS & Environment Foundation**:
     - Configured safe credentialed CORS in `app.config.Settings` and `app.main`.
     - Supports `ALLOWED_ORIGINS` and `FRONTEND_URL` environment variables (defaulting to Vite dev port `http://localhost:5173`, `http://127.0.0.1:5173`, and `http://localhost:3000`).
     - Hardened against unsafe unrestricted credentialed wildcards (`allow_origins=["*"]` strictly prevented when credentials are enabled).
  2. **Standardized JSON Error Schema**:
     - Globally unified error responses across all HTTP status codes:
       - `400 Bad Request` (`HTTP_400`)
       - `401 Unauthorized` (`HTTP_401`)
       - `403 Forbidden` (`HTTP_403`)
       - `404 Not Found` (`HTTP_404`)
       - `422 Unprocessable Entity` (`VALIDATION_ERROR` with structured `"errors"` list)
       - `500 Internal Server Error` (`INTERNAL_SERVER_ERROR`)
     - Predictable format containing `detail`, `status_code`, and `error_code`.
  3. **Locality & Infrastructure Endpoints**:
     - `GET /areas`: Administrative boundaries and neighbourhoods listing.
     - `GET /areas/{area_id}`: Locality metadata lookup.
     - `GET /services`: Cataloged civic facilities with filters (`category_code`, `area_id`, `status`).
     - `GET /services/{service_id}`: Facility detail lookup for map pins and resilience failure simulation.
     - `GET /services/categories`: Active civic service categories list.
  4. **Frontend-Safe Response Serialization**:
     - Validated Pydantic models preventing invalid NaN/infinite floats, missing fields, or null pointer crashes.
     - Safe handling of zero facilities in catchment (deserts return cleanly with indicators).
  5. **Demo Mode Integrity**:
     - 100% offline, reproducible execution with seeded SQLite/PostGIS database.
     - Zero external network dependencies.

- **Files Changed**:
  - `backend/app/config.py`
  - `backend/app/main.py`
  - `backend/app/schemas/infrastructure.py`
  - `backend/app/schemas/errors.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/services.py`
  - `backend/app/routes/areas.py`
  - `backend/app/routes/__init__.py`
  - `backend/tests/test_stage5.py`
  - `.env.example`
  - `backend/.env.example`
  - `backend/.env`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-05.md`

- **Checks Run**:
  - Backend startup: PASS
  - `/health` check: PASS
  - Login & token issuance: PASS
  - `/auth/me` inspection: PASS
  - Invalid/expired token rejection (401): PASS
  - Server-side RBAC enforcement (403): PASS
  - Safe credentialed CORS: PASS
  - Standard error structures (400, 401, 403, 404, 422, 500): PASS
  - All core documented APIs: PASS
  - Frontend-safe determinism: PASS
  - Full regression test suite: PASS (90/90 passing)

- **Known Limitations**:
  - Real-time websocket subscriptions and external GIS tiles belong to later stages.

- **Next Stage**:
  - Stage 6

---

### Stage 6: Map + Core Dashboard Backend
- **Result**: PASS
- **Status**: Map and Core Dashboard Backend Ready for Person 1

- **Features & Enhancements Implemented**:
  1. **Locality Polygon GeoJSON (`GET /areas/geojson`, `GET /areas/{area_id}/geojson`)**:
     - Standard RFC 7946 GeoJSON FeatureCollection and Feature representations.
     - Fully WGS84 CRS compliant polygon/multipolygon geometries parsed via Shapely.
     - Optional analytics property injection (`accessibility_score`, `gap_score`, `desert_classification`, `categories_evaluated`).
     - Supports administrative filtering (`area_type`, `parent_id`).
  2. **Service Point GeoJSON (`GET /services/geojson`)**:
     - Standard GeoJSON Point FeatureCollection for facilities.
     - GeoJSON coordinate order `[longitude, latitude]` for immediate consumption by Leaflet marker layers.
     - Supports filters: `category_code`, `area_id`, `status`.
  3. **Underserved Rankings Leaderboard (`GET /analytics/rankings/underserved`)**:
     - Deterministic prioritization ranking of areas from most underserved to least underserved.
     - Supports composite ranking and category-specific rankings (e.g. healthcare, education, transport, water, market).
     - Deterministic tie-breaking (`-gap_score`, `-population`, `area_id`).
     - Powers the Core Dashboard's "Top Underserved Areas" leaderboard and map quick-filter controls.
  4. **Selected Locality Full Dashboard Metrics (`GET /analytics/areas/{area_id}`)**:
     - Complete, verified scorecard metrics:
       - Accessibility Score (0–100)
       - Gap Score (0–100)
       - Service Desert Classification
       - Population
       - Nearest facility name, distance (km), and travel time (min)
       - Capacity, current load, and service pressure classification
       - Equity score
       - Data confidence score
       - Reality Gap indicators from community ground reports
  5. **Fault-Tolerant & Empty Data Handling**:
     - Safe fallbacks for missing/unlocated geometries (`geometry: None` conforming to RFC 7946).
     - Empty result sets for non-matching filters without exceptions.
     - Zero duplicate calculation logic, strictly leveraging existing Stage 3 analytics engine.

- **Files Changed**:
  - `backend/app/analytics/geojson.py`
  - `backend/app/schemas/geojson.py`
  - `backend/app/schemas/rankings.py`
  - `backend/app/schemas/__init__.py`
  - `backend/app/routes/areas.py`
  - `backend/app/routes/services.py`
  - `backend/app/routes/analytics.py`
  - `backend/tests/test_stage6.py`
  - `API_CONTRACT.md`
  - `BUILD_STATE.md`
  - `docs/checkpoints/STAGE-06.md`

- **Checks Run**:
  - Map / Locality API: PASS
  - Service API: PASS
  - GeoJSON validation: PASS
  - Accessibility / Gap API: PASS
  - Ranking API: PASS
  - Selected-area metrics: PASS
  - Empty-data handling: PASS
  - Stage 3 regression tests: PASS (14/14)
  - Stage 4 regression tests: PASS (51/51)
  - Full test suite: PASS (98/98 passing)
  - Backend startup: PASS

- **Known Limitations**:
  - Vector tile caching (MVT) and WebSockets belong to later stages.

- **Next Stage**:
  - Stage 7


