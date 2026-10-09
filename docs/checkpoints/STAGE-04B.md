# Stage 04B Checkpoint

## Objective
Establish the deterministic recommendation scoring and ranking engine for CivicPulse as Person 2 (Backend / GIS / Analytics). The engine evaluates candidate intervention locations generated in Stage 4A, answers "Which candidate is better?", assigns transparent multi-criteria scores (0–100), executes stable tie-breaking, constructs human-readable explanations, and excludes invalid candidates without performing full intervention simulation.

---

## Implemented
1. **Recommendation Domain & Configuration Layer (`app.decision.recommendation`)**:
   - `RecommendationConfig` Pydantic model with strict validation guaranteeing factor weights sum to 1.0 (100%).
   - `ScoredCandidate` domain model capturing candidate geometry, rank, score, factor breakdown, weights, reasons, and confidence.
   - `RecommendationScoringService` orchestrating factor normalization, composite scoring, stable ranking, and exclusion reporting.
2. **Transparent Multi-Criteria Formula & Normalization**:
   - Strictly normalizes all 7 criteria to [0.0, 100.0] before combination:
     - `gap_severity`: Clamped 0–100 deficit score.
     - `population_affected`: Scaled relative to reference population scale (`ref_population = 25,000`).
     - `travel_time_need`: Inverse travel-time score (`100.0 - travel_time_score`), properly treating unreached catchments as 100% need.
     - `capacity_pressure`: Categorical and numerical load mapping (Critical = 100, High = 75, Moderate = 50, Low = 20).
     - `equity_need`: Demographic and vulnerability baseline prioritization.
     - `connectivity`: Local transit access and transport network connectivity.
     - `data_confidence`: Scaled 0–100 telemetry and verification confidence score.
3. **Deterministic Ranking & Stable Tie-Breaking**:
   - Primary Sort: `recommendation_score` descending.
   - Secondary Sort (Tie-Breaker 1): `population` descending.
   - Tertiary Sort (Tie-Breaker 2): `candidate_id` ascending.
   - Sequential integer ranks assigned starting at 1.
4. **Invalid Candidate Exclusion**:
   - Candidates marked invalid by Stage 4A geospatial validation are not scored.
   - Excluded candidates are safely returned in `excluded_candidates` with recorded rejection reasons.
5. **Civic Explanation Generator**:
   - Dynamically assembles bulleted civic justifications highlighting severe gaps, high populations, travel deficits, and capacity constraints.
6. **API Endpoints (`app.routes.recommendations`)**:
   - `POST /recommendations`: JSON payload supporting custom weight overrides and area filtering.
   - `GET /recommendations`: Query param endpoint for easy retrieval.
   - Registered under OpenAPI tag `"Recommendation Engine"`.
7. **Automated Verification Suite (`tests/test_recommendations.py`)**:
   - 15 dedicated unit and integration tests covering calculation, normalization, boundaries, ranking, tie-breaking, missing data, explanations, and API endpoints.

---

## Recommendation Formula
```
Recommendation Score =
  (Gap Severity × 0.30)
+ (Population Affected × 0.25)
+ (Travel-Time Need × 0.15)
+ (Capacity Pressure × 0.10)
+ (Equity Need × 0.10)
+ (Connectivity × 0.05)
+ (Data Confidence × 0.05)
```
Clamped and rounded: `0.0 <= Recommendation Score <= 100.0`.

---

## Ranking Logic
1. Filter candidates for the service type across underserved areas.
2. Separate into valid and invalid candidate partitions.
3. Compute normalized factor values and composite score for each valid candidate.
4. Sort valid candidates by `(-recommendation_score, -population, candidate_id)`.
5. Assign ranks: `1, 2, 3...` sequentially.
6. Seeded Demo Ranking Highlights:
   - **Healthcare**: Highlands Valley candidates rank #1 (Score: 80.6).
   - **Transport**: Highlands Valley candidates rank #1 (Score: 80.6).
   - **Water**: Riverside Commons candidates rank #1 (Score: 77.3).
   - **Market**: South Hillside candidates rank #1 (Score: 73.6).

---

## API
- `POST /recommendations`
- `GET /recommendations`
Documented in `API_CONTRACT.md`.

---

## Files Changed
- `backend/app/decision/recommendation.py` (New): `RecommendationScoringService` and `RecommendationConfig`.
- `backend/app/decision/__init__.py` (Modified): Exported recommendation service and models.
- `backend/app/schemas/recommendation.py` (New): Pydantic request and response schemas.
- `backend/app/schemas/__init__.py` (Modified): Exported recommendation schemas.
- `backend/app/routes/recommendations.py` (New): FastAPI recommendation endpoints.
- `backend/app/routes/__init__.py` (Modified): Exported `recommendations_router`.
- `backend/app/main.py` (Modified): Registered `recommendations_router` and OpenAPI tag.
- `backend/tests/test_recommendations.py` (New): 15 comprehensive automated test cases.
- `API_CONTRACT.md` (Modified): Updated to version 0.4.2 with Section 5.
- `BUILD_STATE.md` (Modified): Updated to Stage 4B PASS, next Stage 4C.
- `docs/checkpoints/STAGE-04B.md` (New): Checkpoint documentation.

---

## Checks
- recommendation score: PASS
- weight validation: PASS
- normalization: PASS
- score range (0–100): PASS
- ranking: PASS
- tie-breaking: PASS
- invalid candidates: PASS
- missing data: PASS
- explanation: PASS
- service validation: PASS
- Stage 3 regression tests: PASS (14/14 tests passing)
- Stage 4A regression tests: PASS (13/13 tests passing)
- backend startup / OpenAPI: PASS (15 endpoints active)
- recommendation API: PASS
- seeded demo ranking: PASS (60/60 tests passing across all test suites)

---

## Result
**PASS**

---

## Known Limitations
- Does not run intervention simulations (before/after accessibility recalculations) or multi-facility combinatorial budget optimization. Those belong to Stage 4C and Stage 5.

---

## Important Decisions
- Normalization uses a reference population scale of 25,000 to proportionally scale neighborhood demographics without creating out-of-scale bounds.
- Missing values fall back gracefully to neutral defaults (50.0 for unmeasured fields, 100.0 for travel need if no service exists in catchment) without throwing exceptions.

---

## Next Stage
**STAGE 4C**
