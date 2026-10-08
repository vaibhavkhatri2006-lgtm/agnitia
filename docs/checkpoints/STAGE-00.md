# Checkpoint: Stage 0 — Project Foundation

## Objective
Establish the project foundation for CivicPulse as Person 2 (Backend / Database / GIS / AI):
- Set up backend project structure and environment configuration
- Scaffold FastAPI application with operational `/health` endpoint
- Configure database connectivity probe (SQLAlchemy) without creating application tables yet
- Set up Docker and containerized support
- Ensure frontend scaffold is in place and verified
- Establish repository structure, documentation, and checkpoint tracking

---

## Implemented

1. **Repository Structure & Git Setup**:
   - Initialized Git repository with comprehensive `.gitignore` covering Python, Node, database files, and environment files.
   - Clean and focused project layout: `backend/`, `frontend/`, `docs/`, `docker-compose.yml`, `API_CONTRACT.md`, `README.md`, `BUILD_STATE.md`.

2. **Backend Architecture (`backend/`)**:
   - `backend/app/config.py`: Pydantic BaseSettings loading `.env` configuration (Database URL, Host, Port, CORS origins, Environment).
   - `backend/app/database.py`: SQLAlchemy 2.0 engine and sessionmaker configuration, with `check_database_connection()` probe executing `SELECT 1` without creating tables prematurely.
   - `backend/app/main.py`: FastAPI application with CORS middleware, root metadata endpoint (`/`), and health check endpoint (`/health`).
   - `backend/run.py`: Developer runner script for backend with Uvicorn.
   - `backend/start_db.py`: Standalone database connectivity and startup verification script.
   - `backend/Dockerfile` & `docker-compose.yml`: Container specification for backend and PostGIS database services.

3. **Database Foundation**:
   - Configured SQLAlchemy connectivity with connection pre-ping.
   - Supported default zero-dependency SQLite for immediate local development.
   - Supported PostgreSQL + PostGIS via Docker Compose configuration.

4. **Health Check Endpoint**:
   - `GET /health` returns application operational status and database connection probe result (`SELECT 1`).

5. **Tests**:
   - `backend/tests/test_health.py` covering `/` and `/health` endpoints using FastAPI TestClient and pytest.

6. **Frontend Scaffold (`frontend/`)**:
   - Scaffolded Vite + React frontend with validated dependencies and production build.

---

## Files Changed

- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `API_CONTRACT.md`
- `README.md`
- `BUILD_STATE.md`
- `docs/checkpoints/STAGE-00.md`
- `backend/.env.example`
- `backend/.env`
- `backend/Dockerfile`
- `backend/requirements.txt`
- `backend/run.py`
- `backend/start_db.py`
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/tests/__init__.py`
- `backend/tests/test_health.py`
- `frontend/*` (Vite + React scaffold and dependencies)

---

## Commands Run & Verification

1. **Node Check**:
   - Command: `node --version`, `npm.cmd --version`
   - Result: Node v24.14.0, npm 11.9.0 (PASS)

2. **Python Check**:
   - Command: `python --version`
   - Result: Python 3.12.10 (PASS)

3. **Frontend Scaffold Check**:
   - Command: `npx.cmd -y create-vite@latest frontend --template react ...`
   - Command: `npm.cmd --prefix frontend run build`
   - Result: PASS

4. **Database Startup & Verification Check**:
   - Command: `backend\.venv\Scripts\python.exe backend\start_db.py`
   - Result: PASS (`SELECT 1` succeeds)

5. **Backend Startup Check**:
   - Command: `backend\.venv\Scripts\python.exe backend\run.py`
   - Result: PASS (FastAPI / Uvicorn server launches on port 8000)

6. **Health Endpoint Check**:
   - Command: `backend\.venv\Scripts\pytest.exe backend\tests\test_health.py` & HTTP GET `http://127.0.0.1:8000/health`
   - Result: PASS (Status 200, `{"status": "healthy", "database": "connected"}`)

---

## Result
**PASS**

---

## Known Issues
- Docker is not installed on the local Windows environment host; SQLite is used as the default local database. PostGIS Docker configuration is provided in `docker-compose.yml` for environments with Docker installed.

---

## Important Decisions
- Kept SQLite as zero-config default to enable rapid local setup without external database daemon requirements.
- Avoided defining ORM models or database migrations in Stage 0 as strictly instructed.
- Configured CORS middleware early so the frontend scaffold can seamlessly interact with the API in later stages.

---

## Next Stage
**Stage 1** (Authentication, User Management, and Initial Data Models)
