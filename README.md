# CivicPulse

CivicPulse is a modern civic infrastructure, urban accessibility, and community analytics platform designed to empower citizens and urban planners with data-driven insights.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn
- **Database**: SQLite (local development default) / PostgreSQL + PostGIS (via Docker)
- **Frontend Scaffold**: Vite + React
- **DevOps**: Docker & Docker Compose support

---

## Project Structure

```
civicpulse/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py       # Pydantic Settings & environment variables
│   │   ├── database.py     # SQLAlchemy engine, session, & health probe
│   │   └── main.py         # FastAPI application with /health endpoint
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py  # Health check & root endpoint tests
│   ├── .env.example        # Backend environment template
│   ├── Dockerfile          # Backend container specification
│   ├── requirements.txt    # Python backend dependencies
│   ├── run.py              # Backend startup entrypoint
│   └── start_db.py         # Database connection verification & probe
├── frontend/               # Vite + React frontend scaffold
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
- `DATABASE_URL`: Defaults to `sqlite:///./civicpulse.db`
- `BACKEND_HOST`: `127.0.0.1`
- `BACKEND_PORT`: `8000`
- `ENVIRONMENT`: `development`

---

### 2. Database Startup

#### Option A: Local SQLite (Default - Zero External Setup)
SQLite is embedded directly in Python. Run the database startup and connection probe script:

```bash
# Windows
.\backend\.venv\Scripts\python backend\start_db.py

# Linux / macOS
./backend/.venv/bin/python backend/start_db.py
```

#### Option B: Docker Compose (PostgreSQL + PostGIS)
If Docker is installed:

```bash
docker compose up -d db
```

---

### 3. Backend Startup

Set up Python virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv backend/.venv

# Activate and install dependencies (Windows PowerShell)
.\backend\.venv\Scripts\pip install -r backend/requirements.txt

# Start backend server
.\backend\.venv\Scripts\python backend/run.py
```

Or run via Uvicorn directly:
```bash
.\backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at:
- **API Root**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 4. Frontend Startup

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs at [http://localhost:5173](http://localhost:5173).

---

### 5. Running Backend Tests

```bash
.\backend\.venv\Scripts\pytest backend/tests
```
