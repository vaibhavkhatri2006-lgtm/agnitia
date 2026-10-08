# Stage 04C Checkpoint

## Objective
Establish the deterministic What-If / Intervention Simulation engine for CivicPulse as Person 2 (Backend / GIS / Analytics). The simulation answers "What happens if we add a new service at this location?" by comparing baseline service access (BEFORE) with simulated post-intervention access (AFTER) and calculating the measurable impact, all in-memory without permanently modifying the official database.

---

## Implemented
1. **Simulation Domain & Service Layer (`app.decision.simulation`)**:
   - `InterventionSimulationService`: Core engine orchestrating location resolution, baseline evaluation, ephemeral in-memory service injection, post-intervention recalculation, impact delta measurement, and explanation generation.
   - Dual location input modes: supports existing `candidate_id` (from Stage 4A/4B) or direct coordinates (`latitude`, `longitude`).
   - Spatial containment resolution using Shapely geometric boundary checks to identify the target receiving neighbourhood.
2. **In-Memory Ephemeral Intervention Execution**:
   - Extended `AnalyticsEngine` (`analyze_area_category`, `calculate_transport_connectivity`, `analyze_area_overall`) to accept an optional `additional_services: Optional[List[Service]] = None` parameter.
   - Instantiates transient in-memory `Service` and `ServiceCapacity` models strictly within the simulation context.
   - Never calls `db.add()`, `db.merge()`, or `db.commit()`—the official database is 100% untouched.
3. **Multi-Scope Evaluation**:
   - Default city-wide scope evaluates all non-overlapping neighbourhoods (`Downtown Core`, `West End`, `Riverside Commons`, `Highlands Valley`, `South Hillside`).
   - Target area scope / specific area ID allows focused single-locality evaluations.
4. **Impact Delta & Safety Protection**:
   - Calculates accessibility improvement, gap reduction, coverage expansion (percentage points), underserved population reduction, population newly gaining meaningful access, and travel time saved.
   - Safety clamping guarantees non-negative improvement metrics even when intervening in saturated areas.
5. **Civic Explanation & Attribution**:
   - Generates natural language civic justifications detailing the reduction in travel time, elimination of service deserts, and capacity additions.
   - Returns structured `primary_factors` keys (`travel_time_reduction`, `service_desert_resolution`, `underserved_population_relief`, `coverage_expansion`, `capacity_addition`).
6. **API Endpoints (`app.routes.simulations`)**:
   - `POST /simulations`: Accepts JSON payload with `service_type`, `candidate_id` or `(latitude, longitude)`, optional `scope`, `proposed_name`, `proposed_capacity`.
   - `GET /simulations`: Query-parameter variant for testing and rapid exploration.
   - Registered under OpenAPI tag `"Intervention Simulation"`.
7. **Automated Verification Suite (`tests/test_simulations.py`)**:
   - 16 unit and integration tests covering all 12 specified requirements with 100% pass rate.

---

## Simulation Metrics

### Baseline (Before) State
- **Accessibility Score**: Population-weighted composite score (0–100) across areas in scope.
- **Gap Score**: Service gap deficit score (`100.0 - accessibility_score`, 0–100).
- **Service Coverage**: Percentage of population residing in covered areas (`accessibility_score >= 60.0` or desert classification in `["Well Served", "Adequate"]`).
- **Underserved Population**: Total population residing in underserved areas or service deserts.
- **Average Estimated Travel Time**: Population-weighted travel time in minutes to the nearest operational service.

### Post-Intervention (After) State
- Recalculates the exact same 5 standardized metrics with the proposed facility present in-memory.

### Measurable Impact (Delta)
- **Accessibility Improvement**: `after.accessibility_score - before.accessibility_score` (+ points)
- **Gap Reduction**: `before.gap_score - after.gap_score` (- points)
- **Coverage Improvement**: `after.service_coverage - before.service_coverage` (+ percentage points)
- **Underserved Population Reduction**: `before.underserved_population - after.underserved_population` (residents)
- **Population Gaining Meaningful Access**: Residents transitioning from unserved to served.
- **Travel Time Improvement**: `before.average_travel_time_minutes - after.average_travel_time_minutes` (minutes saved)

---

## API

### `POST /simulations`
**Input:**
```json
{
  "service_type": "healthcare",
  "candidate_id": "cand-healthcare-9-centroid",
  "scope": "city",
  "proposed_capacity": 5000
}
```

**Output:**
```json
{
  "simulation_id": "sim-healthcare-cand-healthcare-9-centroid-city",
  "service_type": "healthcare",
  "candidate_id": "cand-healthcare-9-centroid",
  "latitude": 12.978,
  "longitude": 77.625,
  "scope": "city",
  "target_area": {
    "area_id": 9,
    "area_name": "Highlands Valley",
    "area_type": "neighbourhood",
    "population": 22000,
    "before_accessibility": 13.1,
    "after_accessibility": 78.8,
    "accessibility_improvement": 65.7,
    "before_gap": 86.9,
    "after_gap": 21.2,
    "before_classification": "Critical Desert",
    "after_classification": "Adequate",
    "before_travel_time_minutes": 57.9,
    "after_travel_time_minutes": 0.0,
    "travel_time_saved_minutes": 57.9
  },
  "before": {
    "accessibility_score": 65.4,
    "gap_score": 34.6,
    "service_coverage": 76.1,
    "underserved_population": 22000,
    "average_travel_time_minutes": 15.9
  },
  "after": {
    "accessibility_score": 81.1,
    "gap_score": 18.9,
    "service_coverage": 100.0,
    "underserved_population": 0,
    "average_travel_time_minutes": 2.1
  },
  "impact": {
    "accessibility_improvement": 15.7,
    "gap_reduction": 15.7,
    "coverage_improvement": 23.9,
    "underserved_population_reduction": 22000,
    "population_gaining_access": 22000,
    "travel_time_improvement_minutes": 13.8
  },
  "explanation": "The proposed healthcare facility in Highlands Valley improves access because it reduces estimated travel time from 57.9 to 0.0 minutes (57.9 min saved); resolves the Critical Desert status in Highlands Valley; provides meaningful healthcare coverage for 22,000 previously underserved residents; increases overall service coverage by +23.9 percentage points; adds 5,000 units of dedicated capacity relieving service pressure.",
  "primary_factors": [
    "travel_time_reduction",
    "service_desert_resolution",
    "underserved_population_relief",
    "coverage_expansion",
    "capacity_addition"
  ],
  "confidence": 0.9
}
```

---

## Files Changed
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

---

## Checks
1. Simulation calculation: PASS
2. Validation (service types, coordinates, candidates): PASS
3. Before/After consistency: PASS
4. Deterministic output: PASS
5. Database integrity (zero permanent records): PASS
6. Impact calculation (coverage, travel time, population): PASS
7. Explanation & factor attribution: PASS
8. Stage 3 regression tests: PASS (14/14)
9. Stage 4A regression tests: PASS (14/14)
10. Stage 4B regression tests: PASS (15/15)
11. Stage 4C simulation tests: PASS (16/16)
12. Backend startup & OpenAPI: PASS (16 paths)
13. Seeded demo candidate simulation: PASS

---

## Result
PASS

---

## Known Limitations
- Multi-intervention portfolio combinatorial optimization, budget constrained scheduling, and facility degradation/failure simulations belong to Stage 4D and Stage 5.

---

## Next Stage
Stage 4D
