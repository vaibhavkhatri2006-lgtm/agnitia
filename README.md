# CivicPulse

CivicPulse is a modern civic infrastructure, urban accessibility, and community analytics platform designed to empower citizens and urban planners with data-driven insights.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, GeoAlchemy2, Shapely, Uvicorn
- **Database**: PostgreSQL + PostGIS (Production/Docker) / SQLite (Local Development)
- **Frontend Scaffold**: Vite + React
- **DevOps**: Docker & Docker Compose support

---

## Project Structure

```
civicpulse/
├── backend/
│   ├── alembic/            # Alembic migration scripts and environment
│   │   ├── versions/       # Schema version migration scripts
│   │   └── env.py          # Migration execution environment
│   ├── app/
│   │   ├── models/         # SQLAlchemy 2.0 data models
│   │   │   ├── types.py                # SafeGeometry spatial type decorator
│   │   │   ├── data_source.py          # Data source & trust levels
│   │   │   ├── geographic_area.py      # Multi-scale hierarchical areas
│   │   │   ├── service_category.py     # Data-driven categories
│   │   │   ├── service.py              # Civic services with spatial points
│   │   │   ├── service_capacity.py     # Capacities and current load
│   │   │   ├── population_cell.py      # Spatial population & demographics
│   │   │   ├── community_report.py     # Citizen issue reports
│   │   │   ├── report_verification.py  # Verification audits
│   │   │   └── audit_log.py            # Comprehensive mutation tracking
│   │   ├── config.py       # Pydantic Settings & environment variables
│   │   ├── database.py     # SQLAlchemy engine, session, & health probe
│   │   └── main.py         # FastAPI application with /health endpoint
│   ├── tests/
│   │   ├── test_database.py # Stage 1 integrity, geometry, & query tests
│   │   └── test_health.py   # Health check & root endpoint tests
│   ├── seed.py             # Deterministic demo data seeding script
│   ├── verify_stage1.py    # End-to-end verification suite
│   ├── run.py              # Backend startup entrypoint
│   ├── start_db.py         # Database connection verification & probe
│   ├── requirements.txt    # Python backend dependencies
│   ├── Dockerfile          # Backend container specification
│   ├── alembic.ini         # Alembic configuration
│   └── .env.example        # Backend environment template
├── frontend/               # Vite + React frontend scaffold (Person 1)
├── docs/
│   └── checkpoints/        # Stage completion records
├── .env.example            # Root environment template
├── docker-compose.yml      # PostGIS database & containerized backend
├── API_CONTRACT.md         # API contract documentation
├── BUILD_STATE.md          # Multi-stage build state tracking
└── README.md
```

---

## Quickstart Guide

### 1. Environment Setup

Copy `.env.example` to `.env`:

```bash
# Windows PowerShell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env

# Linux / macOS
cp .env.example .env
cp backend/.env.example backend/.env
```

Configuration options:
- `DATABASE_URL`: Defaults to `sqlite:///./civicpulse.db` (or `postgresql+psycopg2://civicpulse:civicpulse_secret@localhost:5432/civicpulse_db`)
- `BACKEND_HOST`: `127.0.0.1`
- `BACKEND_PORT`: `8000`
- `ENVIRONMENT`: `development`

---

### 2. Database Migrations & Deterministic Seeding

#### Run Migrations (Upgrade to Head)
```bash
# Windows PowerShell
.\backend\.venv\Scripts\alembic upgrade head

# Linux / macOS
./backend/.venv/bin/alembic upgrade head
```

#### Downgrade Migrations (Rollback to Base)
```bash
# Windows PowerShell
.\backend\.venv\Scripts\alembic downgrade base

# Linux / macOS
./backend/.venv/bin/alembic downgrade base
```

#### Run Deterministic Seed
Populates the database with reproducible simulated demonstration data (labeled `simulated_demo`):
```bash
# Windows PowerShell
.\backend\.venv\Scripts\python backend/seed.py

# Linux / macOS
./backend/.venv/bin/python backend/seed.py
```

#### Run End-to-End Verification Check
```bash
# Windows PowerShell
.\backend\.venv\Scripts\python backend/verify_stage1.py

# Linux / macOS
./backend/.venv/bin/python backend/verify_stage1.py
```

---

### 3. Backend Startup

```bash
# Start backend server (Windows PowerShell)
.\backend\.venv\Scripts\python backend/run.py

# Or via Uvicorn directly
.\backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at:
- **API Root**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 4. Running Backend Tests

```bash
# Windows PowerShell
.\backend\.venv\Scripts\pytest backend/tests

# Linux / macOS
./backend/.venv/bin/pytest backend/tests
```
