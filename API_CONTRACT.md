# CivicPulse API Contract

## Version: 0.1.0
## Stage: Stage 0 (Project Foundation)

This document establishes the official API contract between the CivicPulse backend and frontend / consumers.

---

### Base URL

- **Development:** `http://127.0.0.1:8000` (or `http://localhost:8000`)
- **Interactive Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI)
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

---

### Stage 0 Endpoints

#### 1. Root Endpoint

- **Method:** `GET`
- **Path:** `/`
- **Description:** Basic API metadata and links.

##### Response `200 OK`
```json
{
  "app": "CivicPulse API",
  "version": "0.1.0",
  "environment": "development",
  "message": "Welcome to the CivicPulse API. Visit /docs for OpenAPI documentation.",
  "health_check": "/health"
}
```

---

#### 2. Health Check

- **Method:** `GET`
- **Path:** `/health`
- **Description:** Verifies operational readiness of the API and database connectivity probe (`SELECT 1`).

##### Response `200 OK` (Healthy)
```json
{
  "status": "healthy",
  "app": "CivicPulse API",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected",
  "database_dialect": "sqlite"
}
```

##### Response `503 Service Unavailable` (Degraded / DB Disconnected)
```json
{
  "status": "degraded",
  "app": "CivicPulse API",
  "version": "0.1.0",
  "environment": "development",
  "database": "disconnected",
  "database_dialect": "unknown",
  "database_error": "<error string>"
}
```

---

### Future Stages (Reserved Endpoints)

The following areas will be expanded in subsequent stages:
- **Stage 1+**: Authentication (`/api/v1/auth/*`), User profiles, RBAC
- **Stage 2+**: Civic infrastructure & GIS data endpoints (`/api/v1/gis/*`, `/api/v1/facilities/*`)
- **Stage 3+**: Accessibility scoring & analytics (`/api/v1/analytics/*`)
- **Stage 4+**: Community reporting & issues (`/api/v1/reports/*`)
- **Stage 5+**: Recommendations & AI agent integration (`/api/v1/ai/*`)
