# Stage 8 Checkpoint — Planner Command Center Backend

## Objective
Provide the backend data and APIs required for the municipal planner command center dashboard. Equip urban planners with decision intelligence including underserved locality rankings, multi-sector service comparisons, facility capacity pressure, demographic equity, ground-truth reality gap indicators, and explainable recommended intervention locations backed by simulation impact analysis.

---

## Implemented

1. **Underserved Area Rankings (`GET /planner/rankings`)**:
   - Ranks civic areas from most underserved to least underserved using deterministic composite gap metrics.
   - Fields: `rank`, `area`, `area_id`, `area_type`, `accessibility`, `gap`, `population`, `main_service_gap`, `priority` (Critical, High, Medium, Low).
   - Deterministic sorting by `(-gap, -population, area_id)`.

2. **Cross-Sector Service Comparison (`GET /planner/service-comparison`)**:
   - Standardized multi-domain comparison across all 5 core civic sectors: `healthcare`, `education`, `transport`, `water`, `market`.
   - Returns comparative scores: `accessibility_score`, `gap_score`, `status` (desert classification), `distance_km`, `travel_time_min`, and `capacity_status`.
   - Supports both city-wide comparative scanning and area-specific filtering.

3. **Facility Capacity Pressure (`GET /planner/capacity-pressure`)**:
   - Compares population demand loads against nominal facility capacities.
   - Fields: `demand`, `capacity`, `pressure` (ratio), `status` (Low, Moderate, High, Critical), and `utilization_pct`.
   - Provides granular breakdown by sector and locality.

4. **Equity & Reality Gap Diagnostics (`GET /planner/equity-reality-gap`, `/planner/equity`, `/planner/reality-gap`)**:
   - **Equity**: Demographic equity score and explainable contributing factors (e.g. vulnerability concentration, travel time barriers, transit connectivity).
   - **Reality Gap**: Nominal GIS map accessibility score vs real-world score adjusted for verified citizen-reported outages, divergence point discrepancy, and data confidence.

5. **Explainable Recommendations (`GET /planner/recommendations`)**:
   - Strictly utilizes existing Stage 4 recommendation engine and Stage 4C intervention simulation engine without duplicate calculation logic.
   - Delivers: `recommended_candidate` (spatial coordinates, area name, population, strategy), `score`, `rank`, `reasons` (transparent multi-factor drivers), `expected_impact` (accessibility improvement points, coverage gain, impact score), and `confidence`.

6. **Unified Command Center Overview (`GET /planner/overview`)**:
   - High-efficiency bundle endpoint consolidating rankings, comparative sector analysis, capacity pressure, and top recommended intervention for dashboard initialization.

7. **Server-Side RBAC Enforcement**:
   - Authority and admin roles granted full access.
   - Standard citizen roles restricted with `403 Forbidden`.
   - Unauthenticated callers rejected with `401 Unauthorized`.

---

## APIs

- `GET /planner/rankings`
- `GET /planner/service-comparison`
- `GET /planner/capacity-pressure`
- `GET /planner/equity-reality-gap`
- `GET /planner/equity`
- `GET /planner/reality-gap`
- `GET /planner/recommendations`
- `GET /planner/overview`

---

## Checks

- Ranking API: **PASS**
- Service Comparison API: **PASS**
- Capacity Pressure API: **PASS**
- Equity / Reality Gap API: **PASS**
- Recommendation API: **PASS**
- Authority Permission Check (RBAC): **PASS**
- Regression Tests (`test_auth.py`, `test_stage6.py`, `test_stage7.py`): **PASS**

---

## Result
**PASS**

---

## Known Issues
- Portfolio multi-facility simultaneous optimization and automated budget constraints belong to future optimization stages.

---

## Next Stage
**STAGE 9**
