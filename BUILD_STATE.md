# CivicPulse Build State Tracking

## Current Status
- **Current Stage**: Stage 2 (Backend Core + Auth)
- **Status**: PASS
- **Next Stage**: Stage 3

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
  - Test Suite: `backend\.venv\Scripts\pytest.exe backend\tests` (18/18 passing)
  - Backend Runner: `backend\.venv\Scripts\python.exe backend\run.py`

- **Known Issues**:
  - None. Server-side RBAC and token validation fully operational.

- **Next Stage**:
  - Stage 3
