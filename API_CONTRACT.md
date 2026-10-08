# CivicPulse API Contract

## Version: 0.4.3
## Stage: Stage 4C (What-If / Intervention Simulation)

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

---

#### 5. Recommendation Scoring Engine (Stage 4B)

Evaluates, scores, explains, and ranks candidate intervention locations deterministically based on multi-dimensional civic criteria.

##### `POST /recommendations`
- **Description:** Scores and ranks candidate intervention locations for a specified service type.
- **Request Body:**
```json
{
  "service_type": "healthcare",
  "area_id": null,
  "min_gap_threshold": 20.0,
  "weights": null
}
```
- **Response `200 OK`**:
```json
{
  "service_type": "healthcare",
  "total_candidates_evaluated": 6,
  "valid_candidates_scored": 6,
  "excluded_candidates_count": 0,
  "weights_used": {
    "gap_weight": 0.3,
    "population_weight": 0.25,
    "travel_need_weight": 0.15,
    "capacity_pressure_weight": 0.1,
    "equity_need_weight": 0.1,
    "connectivity_weight": 0.05,
    "confidence_weight": 0.05
  },
  "ranked_candidates": [
    {
      "candidate_id": "cand-healthcare-9-centroid",
      "service_type": "healthcare",
      "rank": 1,
      "recommendation_score": 80.6,
      "latitude": 12.984123,
      "longitude": 77.632145,
      "area_id": 9,
      "area_name": "Highlands Valley",
      "population": 22000,
      "strategy": "centroid",
      "confidence": 0.5,
      "factor_values": {
        "gap_severity": 86.9,
        "population_affected": 88.0,
        "travel_time_need": 100.0,
        "capacity_pressure": 100.0,
        "equity_need": 40.0,
        "connectivity": 25.0,
        "data_confidence": 50.0
      },
      "factor_weights": {
        "gap_weight": 0.3,
        "population_weight": 0.25,
        "travel_need_weight": 0.15,
        "capacity_pressure_weight": 0.1,
        "equity_need_weight": 0.1,
        "connectivity_weight": 0.05,
        "confidence_weight": 0.05
      },
      "reasons": [
        "Severe healthcare accessibility gap (86.9%) in Highlands Valley",
        "Large affected population (22,000 residents)",
        "Long estimated travel time with no reachable facility in catchment",
        "Limited nearby capacity with critical service load pressure"
      ]
    }
  ],
  "excluded_candidates": []
}
```

##### `GET /recommendations`
- **Description:** GET endpoint for ranked recommendations.
- **Query Parameters:**
  - `service_type` (required string): `healthcare`, `education`, `transport`, `water`, `market`
  - `area_id` (optional int)
  - `min_gap_threshold` (optional float, default: `20.0`)
- **Response `200 OK`**: Same schema as `POST /recommendations`.

---

#### 6. What-If / Intervention Simulation Engine (Stage 4C)

Simulates the impact of adding a proposed civic service at a specific candidate location or coordinate point without modifying the official database. Evaluates before vs after states and calculates measurable improvements.

##### `POST /simulations`
- **Description:** Executes in-memory simulation for a proposed facility.
- **Request Body:**
```json
{
  "service_type": "healthcare",
  "candidate_id": "cand-healthcare-9-centroid",
  "latitude": null,
  "longitude": null,
  "scope": "city",
  "proposed_name": "Highlands Valley Community Health Center",
  "proposed_capacity": 5000
}
```
- **Coordinate-based Request Alternative:**
```json
{
  "service_type": "healthcare",
  "latitude": 12.984123,
  "longitude": 77.632145,
  "scope": "city",
  "proposed_name": "Highlands Valley Community Health Center",
  "proposed_capacity": 5000
}
```
- **Response `200 OK`**:
```json
{
  "simulation_id": "sim-healthcare-cand-healthcare-9-centroid-city",
  "service_type": "healthcare",
  "candidate_id": "cand-healthcare-9-centroid",
  "latitude": 12.978,
  "longitude": 77.625,
  "scope": "city",
  "target_area": {
    "area_id": 9,
    "area_name": "Highlands Valley",
    "area_type": "neighbourhood",
    "population": 22000,
    "before_accessibility": 13.1,
    "after_accessibility": 78.8,
    "accessibility_improvement": 65.7,
    "before_gap": 86.9,
    "after_gap": 21.2,
    "before_classification": "Critical Desert",
    "after_classification": "Adequate",
    "before_travel_time_minutes": 57.9,
    "after_travel_time_minutes": 0.0,
    "travel_time_saved_minutes": 57.9
  },
  "before": {
    "accessibility_score": 65.4,
    "gap_score": 34.6,
    "service_coverage": 76.1,
    "underserved_population": 22000,
    "average_travel_time_minutes": 15.9
  },
  "after": {
    "accessibility_score": 81.1,
    "gap_score": 18.9,
    "service_coverage": 100.0,
    "underserved_population": 0,
    "average_travel_time_minutes": 2.1
  },
  "impact": {
    "accessibility_improvement": 15.7,
    "gap_reduction": 15.7,
    "coverage_improvement": 23.9,
    "underserved_population_reduction": 22000,
    "population_gaining_access": 22000,
    "travel_time_improvement_minutes": 13.8
  },
  "explanation": "The proposed healthcare facility in Highlands Valley improves access because it reduces estimated travel time from 57.9 to 0.0 minutes (57.9 min saved); resolves the Critical Desert status in Highlands Valley; provides meaningful healthcare coverage for 22,000 previously underserved residents; increases overall service coverage by +23.9 percentage points; adds 5,000 units of dedicated capacity relieving service pressure.",
  "primary_factors": [
    "travel_time_reduction",
    "service_desert_resolution",
    "underserved_population_relief",
    "coverage_expansion",
    "capacity_addition"
  ],
  "confidence": 0.9
}
```
- **Error Responses**:
  - `400 Bad Request`:
    - "Unsupported service type '...'. Supported services: healthcare, education, transport, water, market"
    - "Candidate '...' not found for service type '...'"
    - "Either 'candidate_id' or both 'latitude' and 'longitude' must be provided"
  - `422 Unprocessable Entity`: Coordinate values out of bounds ([-90, 90], [-180, 180]) or non-numeric.

##### `GET /simulations`
- **Description:** Query-parameter variant of what-if intervention simulation.
- **Query Parameters:**
  - `service_type` (required string): `healthcare`, `education`, `transport`, `water`, `market`
  - `candidate_id` (optional string): Candidate ID
  - `latitude` (optional float): -90.0 to 90.0
  - `longitude` (optional float): -180.0 to 180.0
  - `scope` (optional string, default: `"city"`): `"city"`, `"neighbourhoods"`, or area ID
  - `proposed_capacity` (optional int, default: `5000`)
- **Response `200 OK`**: Same schema as `POST /simulations`.

