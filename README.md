# CivicPulse

CivicPulse is a modern civic infrastructure, urban accessibility, and community analytics platform designed to empower citizens and urban planners with data-driven insights. It bridges the gap between top-down municipal planning and bottom-up citizen ground reality through deterministic spatial analytics, explainable intervention recommendations, what-if simulations, and a verified civic trust hierarchy.

---

## Key Features

1. **Deterministic Geospatial & Analytics Engine**:
   - Multi-dimensional accessibility scoring evaluating travel times, operational status, capacity pressure, transport connectivity, and demographic equity.
   - Categorical service desert classification: Well Served, Adequate, At Risk, Underserved, and Critical Desert.
   - Ground truth integration calculating **Reality Gap** from citizen ground reports.

2. **Decision & Recommendation Engine**:
   - Algorithmic candidate generation using centroid, population density, and gap-perimeter strategies.
   - Transparent 7-factor normalized recommendation scoring with explainable drivers.

3. **In-Memory What-If Intervention Simulation**:
   - Simulates placement of facilities at candidate locations.
   - Produces measurable impact metrics (+accessibility, +coverage expansion, +underserved relief) with zero database mutation.

4. **Systemic Resilience & Outage Modeling**:
   - Models critical infrastructure failures to detect systemic Single Points of Failure.

5. **Multi-Scale Administrative Hierarchy**:
   - Scope-aware analytics across Local, Neighbourhood, District/Ward, and City levels.

6. **Community Trust & Verification Workflow**:
   - Multi-tier lifecycle: `SUBMITTED` -> `PENDING_REVIEW` -> `COMMUNITY_VERIFIED` -> `AUTHORITY_VERIFIED` -> `OFFICIAL`.
   - Immutable audit trail tracking all state mutations.

7. **Dual Operational Modes**:
   - **DEMO MODE**: 100% deterministic, offline, self-contained dataset for safe presentations and testing.
   - **REAL DATA MODE**: Live OpenStreetMap Overpass API ingestion with coordinate validation, spatial deduplication (<15m), and full data provenance. Enforces strict population integrity (never inventing missing census numbers).

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, GeoAlchemy2, Shapely, PyJWT, Bcrypt, Uvicorn, HTTPX
- **Database**: PostgreSQL + PostGIS (Production/Docker) / SQLite with Shapely (Local Development)
- **Frontend**: Vite + React, TailwindCSS/Vanilla CSS, Leaflet GeoJSON Maps (Person 1)
- **Testing**: Pytest (157 automated tests, 100% pass rate)

---

## Documentation Links

- [SETUP.md](file:///c:/Users/varun/OneDrive/Desktop/ag/SETUP.md): Step-by-step setup and quickstart instructions.
- [PROJECT_REPORT.md](file:///c:/Users/varun/OneDrive/Desktop/ag/PROJECT_REPORT.md): Comprehensive project architecture, engine design, and technical report.
- [DEMO_SCRIPT.md](file:///c:/Users/varun/OneDrive/Desktop/ag/DEMO_SCRIPT.md): 3-minute hackathon demo script and flow.
- [JUDGES_QA.md](file:///c:/Users/varun/OneDrive/Desktop/ag/JUDGES_QA.md): Technical defense and judges' Q&A guide.
- [API_CONTRACT.md](file:///c:/Users/varun/OneDrive/Desktop/ag/API_CONTRACT.md): Stable API contract specifications.
- [BUILD_STATE.md](file:///c:/Users/varun/OneDrive/Desktop/ag/BUILD_STATE.md): Complete multi-stage build progress.

---

## Quickstart Guide

### 1. Environment Setup
```powershell
# Windows PowerShell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
```

### 2. Database Migrations & Deterministic Seeding
```powershell
# Run migrations
.\backend\.venv\Scripts\alembic upgrade head

# Run deterministic demo seed (12 entity types seeded)
.\backend\.venv\Scripts\python backend/seed.py
```

### 3. Demo Accounts for Testing

| Role | Email | Password | Intended Capabilities |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@example.com` | `Citizen123!` | Public map, locality scorecards, create reports |
| **Community** | `community@example.com` | `Community123!` | Citizen access + peer report verification |
| **Authority** | `authority@example.com` | `Authority123!` | Planner command center, official audits, simulations |
| **Admin** | `admin@example.com` | `Admin123!` | Full system administration and moderation |
| **Inactive** | `inactive@example.com` | `Inactive123!` | Disabled account for 403 test validation |

### 4. Running Backend & Frontend

**Backend**:
```powershell
.\backend\.venv\Scripts\python backend/run.py
```
- API Root: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Probe: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

**Frontend**:
```bash
cd frontend
npm run dev
```
- Application: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## Automated Test Verification

Run all automated unit, integration, and E2E tests:
```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```
**Test Results**: **157/157 PASS** across all stages (Stages 0–11 + Real Data Mode).
