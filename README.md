# CivicPulse

CivicPulse is a modern civic infrastructure, urban accessibility, and community analytics platform designed to empower citizens and urban planners with data-driven insights.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, GeoAlchemy2, Shapely, PyJWT, Bcrypt, Uvicorn
- **Database**: PostgreSQL + PostGIS (Production/Docker) / SQLite (Local Development)
- **Frontend Scaffold**: Vite + React (Person 1)
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
│   │   ├── core/           # Security, password hashing (bcrypt), JWT logic
│   │   │   └── security.py
│   │   ├── dependencies/   # Reusable route guards & RBAC authorization
│   │   │   └── auth.py
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
│   │   │   ├── audit_log.py            # Comprehensive mutation tracking
│   │   │   ├── role.py                 # RBAC Role and role_permissions
│   │   │   ├── permission.py           # Granular permissions
│   │   │   └── user.py                 # Users with password hashes & roles
│   │   ├── routes/         # FastAPI API endpoints
│   │   │   └── auth.py     # Authentication, /me, & RBAC test endpoints
│   │   ├── schemas/        # Pydantic v2 request/response models
│   │   │   ├── auth.py
│   │   │   └── errors.py
│   │   ├── services/       # Service layer business logic
│   │   │   └── auth_service.py
│   │   ├── config.py       # Pydantic Settings & environment variables
│   │   ├── database.py     # SQLAlchemy engine, session, & health probe
│   │   └── main.py         # FastAPI application with /health & routers
│   ├── tests/
│   │   ├── test_auth.py     # Authentication, JWT, and RBAC tests
│   │   ├── test_database.py # Database integrity, geometry, & query tests
│   │   └── test_health.py   # Health check & root endpoint tests
│   ├── seed.py             # Deterministic demo data seeding script
│   ├── verify_stage1.py    # Stage 1 verification runner
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
- `DATABASE_URL`: Defaults to `sqlite:///./civicpulse.db` (or PostgreSQL connection string)
- `BACKEND_HOST`: `127.0.0.1`
- `BACKEND_PORT`: `8000`
- `JWT_SECRET_KEY`: Secret signing key (32+ bytes)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: 60

---

### 2. Database Migrations & Deterministic Seeding

```bash
# Run migrations (Windows PowerShell)
.\backend\.venv\Scripts\alembic upgrade head

# Run deterministic demo seed (includes demo users and RBAC roles)
.\backend\.venv\Scripts\python backend/seed.py
```

---

### 3. Demo Accounts for Testing

| Role | Email | Password | Intended Capabilities |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@example.com` | `Citizen123!` | Public statistics, create civic reports |
| **Community** | `community@example.com` | `Community123!` | Citizen + peer report verification |
| **Authority** | `authority@example.com` | `Authority123!` | Municipal planner operations, official audits |
| **Admin** | `admin@example.com` | `Admin123!` | Full system administration |
| **Inactive** | `inactive@example.com` | `Inactive123!` | Disabled account for 403 test validation |

---

### 4. Backend Startup

```bash
# Windows PowerShell
.\backend\.venv\Scripts\python backend/run.py
```

Available endpoints:
- **API Root**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

### 5. Running Automated Backend Tests

```bash
# Windows PowerShell
.\backend\.venv\Scripts\pytest backend/tests
```
