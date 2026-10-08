# CivicPulse API Contract

## Version: 0.4.0
## Stage: Stage 4A (Candidate Location Engine)

This document establishes the official API contract between the CivicPulse backend and frontend / consumers.

---

### Base URL

- **Development:** `http://127.0.0.1:8000` (or `http://localhost:8000`)
- **Interactive Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI)
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema:** `http://127.0.0.1:8000/openapi.json`

---

### Standard HTTP Error Responses

All non-2xx responses follow a predictable JSON schema:
```json
{
  "detail": "Description of error or failure reason",
  "status_code": 401,
  "error_code": "HTTP_401"
}
```

- **401 Unauthorized**: Missing, malformed, invalid signature, or expired JWT.
- **403 Forbidden**: Authenticated caller lacks required role or permissions, or account is disabled.
- **404 Not Found**: Resource does not exist.
- **422 Unprocessable Entity**: Request payload failed Pydantic schema validation.
- **500 Internal Server Error**: Unexpected failure without exposing internal stack traces.

---

### Endpoints

#### 1. Root & Health

##### `GET /`
- **Description:** Root metadata and resource catalog.
- **Response `200 OK`**:
```json
{
  "app": "CivicPulse API",
  "version": "0.2.0",
  "environment": "development",
  "message": "Welcome to the CivicPulse API. Visit /docs for OpenAPI documentation.",
  "health_check": "/health",
  "auth_login": "/auth/login"
}
```

##### `GET /health`
- **Description:** Live health check probe and database connectivity (`SELECT 1`).
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "app": "CivicPulse API",
  "version": "0.2.0",
  "environment": "development",
  "database": "connected",
  "database_dialect": "sqlite"
}
```

---

#### 2. Authentication & RBAC

##### `POST /auth/login`
- **Description:** Authenticates user via email/username and password.
- **Request Body:**
```json
{
  "email": "citizen@example.com",
  "password": "Citizen123!"
}
```
- **Response `200 OK`**:
```json
{
  "access_token": "<jwt_bearer_token>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "citizen@example.com",
    "username": "citizen_demo",
    "display_name": "Demo Citizen",
    "role": "citizen",
    "permissions": ["data:read", "report:create"],
    "is_active": true,
    "created_at": "2026-10-08T18:00:00Z"
  }
}
```
- **Error Responses**:
  - `401 Unauthorized`: "Incorrect email or password"
  - `403 Forbidden`: "User account is inactive"

---

##### `GET /auth/me`
- **Description:** Returns profile and server-validated permissions for the currently authenticated caller.
- **Headers:** `Authorization: Bearer <jwt_token>`
- **Response `200 OK`**:
```json
{
  "id": 1,
  "email": "citizen@example.com",
  "username": "citizen_demo",
  "display_name": "Demo Citizen",
  "role": "citizen",
  "permissions": ["data:read", "report:create"],
  "is_active": true,
  "created_at": "2026-10-08T18:00:00Z"
}
```

---

##### `GET /auth/verify-role/authority`
- **Description:** Protected test endpoint requiring `authority` or `admin` role.
- **Headers:** `Authorization: Bearer <jwt_token>`
- **Response `200 OK`** (for Authority / Admin):
```json
{
  "status": "authorized",
  "message": "Access granted for official authority operation to user 'authority@example.com'",
  "role": "authority",
  "user_id": 3,
  "user_email": "authority@example.com",
  "granted_permissions": ["data:read", "report:create", "report:verify_community", "report:verify_official", "authority:operate"]
}
```
- **Response `403 Forbidden`** (for Citizen / Community):
```json
{
  "detail": "Access denied: Operation requires one of the following roles: authority, admin. Current role: 'citizen'",
  "status_code": 403,
  "error_code": "HTTP_403"
}
```

---

##### `GET /auth/verify-role/admin`
- **Description:** Protected test endpoint requiring `admin` role.
- **Headers:** `Authorization: Bearer <jwt_token>`
- **Response `200 OK`** (for Admin):
```json
{
  "status": "authorized",
  "message": "Access granted for system administrative operation to user 'admin@example.com'",
  "role": "admin",
  "user_id": 4,
  "user_email": "admin@example.com",
  "granted_permissions": ["data:read", "report:create", "report:verify_community", "report:verify_official", "authority:operate", "admin:manage"]
}
```
- **Response `403 Forbidden`** (for non-admin roles).

---

##### `GET /auth/verify-role/community`
- **Description:** Protected test endpoint requiring `community`, `authority`, or `admin` role.
- **Headers:** `Authorization: Bearer <jwt_token>`
- **Response `200 OK`** (for Community / Authority / Admin)
- **Response `403 Forbidden`** (for Citizen)

---

### Demo Accounts for Testing

| Role | Email | Password | Allowed Scopes |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@example.com` | `Citizen123!` | Public views, create civic reports |
| **Community** | `community@example.com` | `Community123!` | Citizen + peer report verification |
| **Authority** | `authority@example.com` | `Authority123!` | Planner operations, official verification |
| **Admin** | `admin@example.com` | `Admin123!` | Full system administration |
| **Inactive** | `inactive@example.com` | `Inactive123!` | Disabled (403 test account) |

---

#### 3. Geospatial & Analytics Engine (Stage 3)

The backend owns all civic computations, ensuring deterministic, reproducible scores across areas and service categories.

##### `GET /analytics/config`
- **Description:** Returns the central analytics configuration containing component weights, speed models, availability score mappings, travel time thresholds, and desert classification categories.
- **Response `200 OK`**:
```json
{
  "travel_time_weight": 0.3,
  "availability_weight": 0.2,
  "capacity_weight": 0.2,
  "transport_weight": 0.15,
  "equity_weight": 0.15,
  "travel_speeds_kmh": {
    "walking": 4.5,
    "transit": 22.0,
    "driving": 35.0
  },
  "availability_scores": {
    "operational": 100.0,
    "limited": 60.0,
    "degraded": 50.0,
    "temporarily_unavailable": 20.0,
    "closed": 0.0
  },
  "travel_time_thresholds": [
    [10.0, 100.0],
    [20.0, 80.0],
    [30.0, 60.0],
    [45.0, 35.0],
    [null, 10.0]
  ],
  "desert_classifications": [
    [80.0, "Well Served"],
    [60.0, "Adequate"],
    [40.0, "At Risk"],
    [20.0, "Underserved"],
    [0.0, "Critical Desert"]
  ]
}
```

##### `GET /analytics/areas`
- **Description:** Returns summary accessibility and gap scores for all geographic areas.
- **Query Parameters:** `include_breakdown` (boolean, default: `false`).
- **Response `200 OK`**:
```json
[
  {
    "area_id": 9,
    "area_name": "Highlands Valley",
    "area_type": "neighbourhood",
    "population": 22000,
    "composite_accessibility_score": 53.4,
    "composite_gap_score": 46.6,
    "composite_desert_classification": "At Risk",
    "categories_evaluated": 5,
    "category_breakdown": null
  }
]
```

##### `GET /analytics/areas/{area_id}`
- **Description:** Returns detailed accessibility metrics and category breakdown for a specific geographic area.
- **Response `200 OK`**: Contains `category_breakdown` array with each service category's metrics.

##### `GET /analytics/areas/{area_id}/category/{category_code}`
- **Description:** Returns category-specific deterministic metrics for an area.
- **Response `200 OK`**:
```json
{
  "area_id": 9,
  "area_name": "Highlands Valley",
  "area_type": "neighbourhood",
  "category_id": 1,
  "category_code": "healthcare",
  "category_name": "Healthcare",
  "nearest_service_id": null,
  "nearest_service_name": null,
  "nearest_service_status": null,
  "distance_km": null,
  "travel_time_minutes": null,
  "travel_time_score": 0.0,
  "availability_score": 0.0,
  "capacity_score": 0.0,
  "transport_connectivity_score": 25.0,
  "equity_score": 35.0,
  "accessibility_score": 9.0,
  "gap_score": 91.0,
  "service_desert_classification": "Critical Desert",
  "service_pressure": {
    "capacity_score": 0.0,
    "pressure_ratio": 999.0,
    "pressure_category": "Critical",
    "pressure_score": 0.0,
    "capacity": 0,
    "current_load": 0,
    "data_quality": "no_service_in_catchment"
  },
  "confidence_score": 0.5,
  "reality_gap_score": 0.0,
  "reality_gap_level": "None",
  "reality_gap_summary": "Ground reports align with reported status"
}
```

##### `GET /analytics/deserts`
- **Description:** Scans all areas and active categories for service deserts (`accessibility_score <= max_score`, default `39.9`).
- **Query Parameters:** `category_code` (optional string), `max_score` (optional float, default `39.9`).
- **Response `200 OK`**:
```json
[
  {
    "area_id": 9,
    "area_name": "Highlands Valley",
    "category_code": "healthcare",
    "category_name": "Healthcare",
    "accessibility_score": 9.0,
    "gap_score": 91.0,
    "service_desert_classification": "Critical Desert",
    "nearest_service_name": null,
    "distance_km": null,
    "pressure_category": "Critical"
  }
]
```

---

#### 4. Decision & Candidate Engine (Stage 4A)

Generates and validates deterministic candidate locations for new civic facilities without deciding final recommendation rankings or simulations.

##### `GET /decision/candidates`
- **Description:** Generates deterministic candidate locations for a specified service type across qualifying underserved areas.
- **Query Parameters:**
  - `service_type` (required string): `healthcare`, `education`, `transport`, `water`, `market`
  - `min_gap_threshold` (optional float, default: `20.0`): Minimum gap score for an area to qualify
  - `max_accessibility` (optional float, default: `80.0`): Excludes areas already sufficiently served
  - `include_rejected` (optional boolean, default: `false`): Whether to include rejected points
- **Response `200 OK`**:
```json
{
  "service_type": "healthcare",
  "total_candidates": 3,
  "valid_candidates_count": 3,
  "rejected_candidates_count": 0,
  "candidates": [
    {
      "candidate_id": "cand-healthcare-9-centroid",
      "service_type": "healthcare",
      "latitude": 12.984123,
      "longitude": 77.632145,
      "area_id": 9,
      "area_name": "Highlands Valley",
      "source_reason": "Geometric interior center of underserved area Highlands Valley (Gap: 86.9%)",
      "current_accessibility": 13.1,
      "population": 22000,
      "current_gap": 86.9,
      "nearby_service_count": 0,
      "validity_status": "valid",
      "strategy": "centroid",
      "rejection_reason": null
    }
  ]
}
```

##### `POST /decision/candidates/generate`
- **Description:** Generates candidates using JSON payload configuration.
- **Request Body:**
```json
{
  "service_type": "water",
  "min_gap_threshold": 20.0,
  "max_accessibility": 80.0,
  "include_rejected": false
}
```
- **Response `200 OK`**: Same schema as `GET /decision/candidates`.
- **Error Response `400 Bad Request`**: For unsupported service types.
```json
{
  "detail": "Unsupported service type 'spaceship_depot'. Supported services: healthcare, education, transport, water, market",
  "status_code": 400,
  "error_code": "HTTP_400"
}
```
