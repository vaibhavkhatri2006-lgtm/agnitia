# CivicPulse — Project Report

## 1. Executive Summary

Rapid urbanization and historical disinvestment have created acute spatial inequalities in cities worldwide. Essential civic infrastructure—clinics, schools, clean water points, public transit stations, and food markets—is often distributed unevenly, producing severe "service deserts" where vulnerable communities endure excessive travel times and overburdened facilities.

**CivicPulse** is an urban accessibility, civic infrastructure resilience, and community analytics platform. Built with mathematical rigor and open standards, CivicPulse bridges the gap between top-down municipal planning and bottom-up citizen ground reality. It empowers urban planners with deterministic spatial analytics, explainable intervention recommendations, and what-if simulation tools, while incorporating citizen-reported infrastructure failures through a verified civic trust hierarchy.

---

## 2. System Architecture

CivicPulse is organized around a modular, decoupled architecture:

```
[ Frontend: React + Leaflet Map ]
              │ (HTTP / JSON / GeoJSON RFC 7946)
              ▼
[ FastAPI Backend Engine ]
  ├── Auth & RBAC (Citizen, Community, Authority, Admin)
  ├── Geospatial & Analytics Engine (Haversine, Urban Detour, Scorecards)
  ├── Decision & Candidate Engine (Centroid, Population Density, Gap Perimeter)
  ├── Recommendation Scoring Engine (7-Factor Transparent Normalized Weights)
  ├── What-If Simulation Engine (In-Memory Before vs After Impact Analysis)
  ├── Systemic Resilience Engine (Outage Modeling & Single Point of Failure)
  ├── Multi-Scale Hierarchy Service (Local, Neighbourhood, Ward, City)
  ├── Community Trust & Moderation (Multi-tier Verification Workflow)
  └── Real Data Ingestion (Overpass API, Deduplication, Provenance Tracking)
              │
              ▼
[ Database Layer: SQLite / PostgreSQL with PostGIS & Shapely ]
```

---

## 3. Core Analytical Engines

### A. Geospatial Accessibility & Desert Scoring
Rather than relying solely on simple Euclidean radius buffers, CivicPulse evaluates access across five calibrated dimensions:
1. **Travel Time (30%)**: Detour-modeled network transit/walking speeds mapped against access thresholds.
2. **Service Availability (20%)**: Operational status of nearest facility (`operational`, `limited`, `degraded`, `temporarily_unavailable`, `closed`).
3. **Capacity Pressure (20%)**: Demographic demand versus nominal facility throughput ($D/C$ ratio), classifying pressure from *Low* to *Critical*.
4. **Transport Connectivity (15%)**: Multimodal proximity to public transit stops.
5. **Demographic Equity (15%)**: Equity weighting prioritizing communities with high demographic vulnerability.

- **Gap Score**: Defined deterministically as $\text{Gap Score} = 100.0 - \text{Accessibility Score}$.
- **Service Desert Classification**:
  * $80 - 100$: Well Served
  * $60 - 79$: Adequate
  * $40 - 59$: At Risk
  * $20 - 39$: Underserved
  * $0 - 19$: Critical Desert

### B. Candidate Location Allocation
When an area is identified as underserved, candidate infrastructure locations are algorithmically generated using three complementary spatial strategies:
- **Centroid**: Interior geographic center of the underserved polygon.
- **Population Node**: Maximum density cluster derived from fine-grained population cells.
- **Gap Perimeter**: Maximum-distance point furthest from all existing facilities to eliminate geographic blind spots.

All candidate locations are checked for geometric boundary containment using Shapely and spatially deduplicated within an 11-meter tolerance.

### C. Multi-Factor Recommendation Scoring
Candidates are scored and ranked transparently without opaque black-box AI:
$$\text{Score} = 0.30 \times \text{Gap} + 0.25 \times \text{Pop} + 0.15 \times \text{Travel} + 0.10 \times \text{Capacity} + 0.10 \times \text{Equity} + 0.05 \times \text{Connectivity} + 0.05 \times \text{Confidence}$$
Every score includes natural language justifications identifying the primary drivers behind the recommendation.

### D. In-Memory What-If Intervention Simulation
To evaluate prospective capital expenditures before investing public funds, planners can simulate placing facilities at candidate locations. The simulation engine runs entirely in-memory:
- Computes baseline accessibility, coverage, underserved population, and travel times.
- Re-evaluates all metrics with the simulated facility added.
- Produces delta metrics: points gained, residents relieved, and minutes saved.
- **Strict Safety Guarantee**: Zero database writes or schema modifications occur during simulation.

### E. Systemic Resilience & Failure Analysis
CivicPulse can model the catastrophic failure or outage of any existing facility. It computes the resulting coverage loss, accessibility drop, and newly underserved population, flagging whether the facility constitutes a **Single Point of Failure**.

---

## 4. Community Ground Truth & Civic Trust

Official maps frequently diverge from ground reality (e.g., a clinic listed as operational may lack electricity or medicine). CivicPulse introduces a **Reality Gap Index** derived from citizen reports:
- **Report Submission**: Citizens submit geo-located reports with severity ratings and optional evidence metadata.
- **Multi-Tier Verification Workflow**:
  $$\text{SUBMITTED} \longrightarrow \text{PENDING\_REVIEW} \longrightarrow \text{COMMUNITY\_VERIFIED} \longrightarrow \text{AUTHORITY\_VERIFIED} \longrightarrow \text{OFFICIAL}$$
- **Role Permissions**:
  * *Citizen*: Submits reports; cannot approve official status.
  * *Community Member*: Conducts peer verification up to `COMMUNITY_VERIFIED`.
  * *Authority*: Approves `OFFICIAL` status or rejects false reports.
  * *Admin*: Complete moderation and oversight.
- **Immutable Audit Trail**: Every status change creates a cryptographically traceable `AuditLog` entry.

---

## 5. Dual Operational Modes: Demo vs Real Data

CivicPulse provides a clear operational separation:
1. **DEMO MODE (Default)**:
   - Self-contained, deterministic synthetic dataset of "Metro City".
   - 100% offline; requires no API keys or internet connection.
   - Guaranteed stability for presentations and automated QA.
2. **REAL DATA MODE**:
   - Queries OpenStreetMap via Overpass API for user-selected localities across 5 categories: Healthcare, Education, Transport, Water, and Market.
   - Validates coordinates and rejects invalid points (including (0,0) Null Island).
   - Spatial deduplication prevents duplicate pins within 15 meters.
   - **Data Integrity**: Never invents or fabricates missing census population. Documented public census data is stored when available; otherwise marked as `"unavailable"`.
   - Records full data provenance (OSM element ID, raw tags, retrieval timestamp, ODbL attribution).
   - Respectful API compliance: SHA256 query caching (24h TTL) and minimum 1.0s query cooldown.

---

## 6. Verification & Quality Assurance

- **Unit, Integration & E2E Tests**: **157 passing tests** across 17 test suites with 0 failures.
- **Performance**:
  - Full regression test suite completes in ~34 seconds.
  - Frontend production bundle builds in under 1 second (771ms).
  - Linter (`oxlint`) passes with 0 warnings and 0 errors across 104 rules.
- **Security**: Stateless HS256 JWT tokens, 12-round bcrypt password hashing, and server-side RBAC guards on all protected routes.
