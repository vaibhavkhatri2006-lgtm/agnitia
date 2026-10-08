# CivicPulse Setup & Quickstart Guide

This guide provides instructions to run CivicPulse locally on Windows, macOS, or Linux.

---

## Prerequisites

- **Python**: Version 3.11 or 3.12
- **Node.js**: Version 18+ and npm
- **Git**

---

## 1. Clone & Repository Layout

```bash
git clone <repo-url>
cd ag
```

---

## 2. Environment Configuration

Copy the example environment templates:

### Windows PowerShell:
```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
```

### Linux / macOS:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Key environment settings in `.env`:
- `DATABASE_URL`: Defaults to `sqlite:///./civicpulse.db` (local dev) or `postgresql+psycopg2://...` (production)
- `CIVICPULSE_MODE`: `demo` (offline synthetic dataset) or `real` (live OpenStreetMap ingestion)
- `USE_OSRM`: `false` (uses deterministic urban detour approximation; set `true` with `OSRM_BASE_URL` if OSRM is running)
- `JWT_SECRET_KEY`: Random 32+ character signing key

---

## 3. Backend Setup & Python Virtual Environment

### Windows PowerShell:
```powershell
# Navigate to backend
cd backend

# Create virtual environment if not already created
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run database migrations
.\.venv\Scripts\alembic.exe upgrade head

# Seed deterministic demo dataset
.\.venv\Scripts\python.exe seed.py

# Return to project root
cd ..
```

### Linux / macOS:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
cd ..
```

---

## 4. Frontend Setup

### Windows / Linux / macOS:
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 5. Starting the Application

### Start the FastAPI Backend:
In Terminal 1 (from project root):
```powershell
# Windows PowerShell
.\backend\.venv\Scripts\python.exe backend\run.py
```
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`

### Start the React Frontend:
In Terminal 2 (from `frontend/` directory):
```bash
# Windows (cmd.exe or PowerShell)
cd frontend
npm run dev
```
- **Frontend App**: `http://127.0.0.1:5173`

---

## 6. Demo Accounts & Credentials

| Role | Email | Password | Permissions & Intended Use |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@example.com` | `Citizen123!` | Public map, locality scorecards, submit citizen reports |
| **Community** | `community@example.com` | `Community123!` | Citizen access + verify community reports |
| **Authority** | `authority@example.com` | `Authority123!` | Planner command center, official verification, simulation lab |
| **Admin** | `admin@example.com` | `Admin123!` | Full moderation, system configuration, audit logs |
| **Inactive** | `inactive@example.com` | `Inactive123!` | Test account for 403 Forbidden verification |

---

## 7. Running Backend Tests

Run all 157 automated tests across all stages:
```powershell
# Windows PowerShell (from project root)
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/ -v
```

---

## 8. Operational Modes

### DEMO MODE (Default)
- 100% deterministic, offline, self-contained dataset.
- Requires zero API keys or external internet connectivity.
- Guaranteed safe for hackathon presentations, judging, and regression testing.

### REAL DATA MODE
- Ingests real-world OpenStreetMap facilities via Overpass API for any user-selected locality or bounding box.
- Preserves documented public census records without synthesizing missing population numbers.
- Stores complete data provenance (OSM element ID, raw tags, retrieval timestamp, ODbL attribution) in immutable audit logs.
- Can be toggled live via `POST /mode` with `{"mode": "real"}`.
