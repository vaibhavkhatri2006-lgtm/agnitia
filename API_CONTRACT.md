# CivicPulse API Contract

## Version: 0.6.0
## Stage: Stage 6 (Map + Core Dashboard Backend)

This document establishes the official API contract between the CivicPulse backend and frontend / consumers.

---

### Base URL & Configuration for Frontend (Person 1)

- **Development Backend:** `http://127.0.0.1:8000` (or `http://localhost:8000`)
- **Frontend Development Origin:** `http://localhost:5173` (Vite)
- **Interactive Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI)
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema:** `http://127.0.0.1:8000/openapi.json`

#### Frontend Environment Variables (`.env` in frontend)
```bash
VITE_API_URL=http://localhost:8000
```

#### CORS & Credentials
- Preconfigured to allow origins: `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`.
- Credentials (`Access-Control-Allow-Credentials: true`) are enabled safely without unrestricted wildcards.
- Pass Bearer token via standard header: `Authorization: Bearer <access_token>`.

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

- **400 Bad Request** (`HTTP_400`): Malformed input or invalid business parameter (e.g., unsupported service type).
- **401 Unauthorized** (`HTTP_401`): Missing, malformed, invalid signature, or expired JWT.
- **403 Forbidden** (`HTTP_403`): Authenticated caller lacks required role or permissions, or account is disabled.
- **404 Not Found** (`HTTP_404`): Resource does not exist (e.g., area ID or service ID not found).
- **422 Unprocessable Entity** (`VALIDATION_ERROR`): Request payload failed Pydantic schema validation. Includes `"errors"` array with field details.
- **500 Internal Server Error** (`INTERNAL_SERVER_ERROR`): Unexpected failure without exposing internal stack traces.

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

#### 3. Localities & Geographic Areas (Stage 5 & Stage 6)

##### `GET /areas/geojson`
- **Description:** Returns all administrative areas, wards, and neighbourhoods formatted as an RFC 7946 GeoJSON `FeatureCollection`. Ideal for direct rendering by frontend Leaflet or MapLibre `<GeoJSON />` layers.
- **Query Parameters:**
  - `area_type` (optional string): Filter by `city`, `ward`, `neighbourhood`
  - `parent_id` (optional int): Filter by parent area ID
  - `include_analytics` (optional boolean, default: `true`): Attaches composite accessibility, gap, and desert classification to feature properties
- **Response `200 OK`**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 9,
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[77.61, 12.965], [77.64, 12.965], [77.64, 12.99], [77.61, 12.99], [77.61, 12.965]]]]
      },
      "properties": {
        "id": 9,
        "name": "Highlands Valley",
        "area_type": "neighbourhood",
        "parent_id": 4,
        "population": 22000,
        "accessibility_score": 53.4,
        "gap_score": 46.6,
        "desert_classification": "At Risk",
        "categories_evaluated": 5
      }
    }
  ]
}
```

##### `GET /areas`
- **Description:** Lists administrative areas, wards, and neighbourhoods for UI map boundaries and dropdowns.
- **Query Parameters:**
  - `area_type` (optional string): Filter by `city`, `ward`, `neighbourhood`
  - `parent_id` (optional int): Filter by parent area ID
- **Response `200 OK`**:
```json
[
  {
    "id": 9,
    "name": "Highlands Valley",
    "area_type": "neighbourhood",
    "parent_id": 4,
    "population": 22000
  }
]
```

##### `GET /areas/{area_id}/geojson`
- **Description:** Returns single locality boundary and properties as an RFC 7946 GeoJSON `Feature`.
- **Query Parameters:**
  - `include_analytics` (optional boolean, default: `true`)
- **Response `200 OK`**: Same schema as individual feature in `GET /areas/geojson`.
- **Error Response `404 Not Found`**:
```json
{
  "detail": "Geographic area with id 9999 not found",
  "status_code": 404,
  "error_code": "HTTP_404"
}
```

##### `GET /areas/{area_id}`
- **Description:** Returns metadata for a specific geographic locality.
- **Response `200 OK`**:
```json
{
  "id": 9,
  "name": "Highlands Valley",
  "area_type": "neighbourhood",
  "parent_id": 4,
  "population": 22000
}
```
- **Error Response `404 Not Found`**:
```json
{
  "detail": "Geographic area with id 9999 not found",
  "status_code": 404,
  "error_code": "HTTP_404"
}
```

---

#### 4. Services & Infrastructure (Stage 5 & Stage 6)

##### `GET /services/categories`
- **Description:** Returns all active civic service categories with codes and names.
- **Response `200 OK`**:
```json
[
  {
    "id": 1,
    "code": "healthcare",
    "name": "Healthcare",
    "description": "Primary healthcare clinics, hospitals, and medical centers",
    "icon": null,
    "is_active": true
  }
]
```

##### `GET /services/geojson`
- **Description:** Returns all cataloged facilities formatted as an RFC 7946 GeoJSON Point `FeatureCollection`. Ideal for direct consumption by Leaflet marker layers.
- **Query Parameters:**
  - `category_code` (optional string): e.g. `healthcare`, `education`, `transport`, `water`, `market`
  - `area_id` (optional int): e.g. `9`
  - `status` (optional string): `operational`, `degraded`, `temporarily_unavailable`, `closed`
- **Response `200 OK`**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,
      "geometry": {
        "type": "Point",
        "coordinates": [77.59, 12.975]
      },
      "properties": {
        "id": 1,
        "name": "Central Metro Hospital",
        "category_id": 1,
        "category_code": "healthcare",
        "category_name": "Healthcare",
        "area_id": 6,
        "area_name": "Downtown Core",
        "latitude": 12.975,
        "longitude": 77.59,
        "status": "operational",
        "source_type": "simulated_demo",
        "verification_status": "verified",
        "confidence_score": 0.98,
        "capacity": 500,
        "current_load": 380,
        "operating_hours": "24/7 Emergency & Inpatient"
      }
    }
  ]
}
```

##### `GET /services`
- **Description:** Lists cataloged civic facilities for rendering pins on map layers and populating dropdown selectors.
- **Query Parameters:**
  - `category_code` (optional string): e.g. `healthcare`, `education`, `transport`, `water`, `market`
  - `area_id` (optional int): e.g. `9`
  - `status` (optional string): `operational`, `degraded`, `temporarily_unavailable`, `closed`
- **Response `200 OK`**:
```json
[
  {
    "id": 1,
    "name": "Central Metro Hospital",
    "category_id": 1,
    "category_code": "healthcare",
    "category_name": "Healthcare",
    "area_id": 6,
    "area_name": "Downtown Core",
    "latitude": 12.975,
    "longitude": 77.59,
    "status": "operational",
    "source_type": "simulated_demo",
    "verification_status": "verified",
    "confidence_score": 0.98,
    "capacity": 500,
    "current_load": 380,
    "operating_hours": "24/7 Emergency & Inpatient"
  }
]
```

##### `GET /services/{service_id}`
- **Description:** Retrieves detailed attributes of a single civic service facility.
- **Response `200 OK`**: Same schema as individual item in `GET /services`.
- **Error Response `404 Not Found`**:
```json
{
  "detail": "Service with id 9999 not found",
  "status_code": 404,
  "error_code": "HTTP_404"
}
```

---

#### 5. Geospatial & Analytics Engine (Stage 3)

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

##### `GET /analytics/rankings/underserved`
- **Description:** Ranks civic areas from most underserved to least underserved using deterministic analytics. Powers the Core Dashboard's "Top Underserved Areas" leaderboard and map priority filters.
- **Query Parameters:**
  - `category_code` (optional string): e.g. `healthcare`, `education`, `transport`, `water`, `market` (omit for composite ranking across all categories)
  - `limit` (optional int, default: `10`, range: `1` to `100`): Maximum number of ranked areas to return
  - `min_gap` (optional float, default: `0.0`): Minimum gap score threshold to include
- **Response `200 OK`**:
```json
{
  "category_evaluated": "composite",
  "total_areas_evaluated": 5,
  "underserved_areas_count": 2,
  "rankings": [
    {
      "rank": 1,
      "area_id": 9,
      "area_name": "Highlands Valley",
      "area_type": "neighbourhood",
      "population": 22000,
      "accessibility_score": 53.4,
      "gap_score": 46.6,
      "desert_classification": "At Risk",
      "category_evaluated": "composite",
      "most_critical_category": "healthcare",
      "nearest_service_name": null,
      "service_pressure_category": null,
      "confidence_score": 1.0
    }
  ]
}
```

---

#### 6. Decision & Candidate Engine (Stage 4A)

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

#### 7. Recommendation Scoring Engine (Stage 4B)

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

#### 8. What-If / Intervention Simulation Engine (Stage 4C)

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

---

#### 9. Investment, Resilience & Future-Risk Engine (Stage 4D)

##### `POST /decision/investment-priorities`
- **Description:** Ranks candidate intervention opportunities by strategic civic investment priority score.
- **Request Body:**
```json
{
  "service_type": "healthcare",
  "min_gap_threshold": 20.0,
  "max_results": 10
}
```
- **Response `200 OK`**:
```json
{
  "service_type": "healthcare",
  "total_interventions_evaluated": 6,
  "ranked_investments": [
    {
      "rank": 1,
      "candidate_id": "cand-healthcare-9-centroid",
      "service_type": "healthcare",
      "area_id": 9,
      "area_name": "Highlands Valley",
      "latitude": 12.978,
      "longitude": 77.625,
      "investment_priority_score": 76.4,
      "priority_tier": "High Priority",
      "recommendation_score": 80.6,
      "expected_impact_score": 81.8,
      "population_affected": 22000,
      "gap_severity": 86.9,
      "equity_need": 40.0,
      "estimated_cost_tier": "Standard Civic Facility (Tier 1)",
      "rationale": "Strategic investment in Highlands Valley: addresses severe healthcare deficit (86.9% gap), serves 22,000 residents with expected accessibility gain of +65.7 points and strong recommendation alignment (80.6/100).",
      "primary_drivers": [
        "critical_service_gap",
        "high_accessibility_impact",
        "large_beneficiary_population"
      ]
    }
  ]
}
```

##### `GET /decision/investment-priorities`
- **Description:** GET endpoint for ranked investment priorities.
- **Query Parameters:** `service_type` (optional), `min_gap_threshold` (optional, default: 20.0), `max_results` (optional, default: 10).

##### `POST /decision/failure-simulation`
- **Description:** Simulates facility outage/failure in-memory to measure systemic resilience, affected population, accessibility drop, and identify single points of failure.
- **Request Body:**
```json
{
  "service_id": 3,
  "scope": "city"
}
```
- **Response `200 OK`**:
```json
{
  "service_id": 3,
  "service_name": "Riverside Health Center",
  "category_code": "healthcare",
  "category_name": "Healthcare",
  "location_area_name": "Riverside Commons",
  "scope": "city",
  "baseline_accessibility": 65.4,
  "failure_accessibility": 52.8,
  "accessibility_drop": 12.6,
  "baseline_coverage": 76.1,
  "failure_coverage": 56.5,
  "coverage_loss": 19.6,
  "directly_affected_population": 18000,
  "newly_underserved_population": 18000,
  "resilience_score": 51.7,
  "criticality_tier": "Critical Infrastructure / Single Point of Failure",
  "single_point_of_failure": true,
  "explanation": "Simulated failure of 'Riverside Health Center' (Healthcare) in Riverside Commons reduces average accessibility by 12.6 points; causes 19.6 percentage points loss in service coverage; throws 18,000 residents into newly underserved status; directly disconnects 18,000 residents who rely on this facility. Systemic resilience rating: 51.7/100 (Critical Infrastructure / Single Point of Failure).",
  "affected_areas": [
    {
      "area_id": 8,
      "area_name": "Riverside Commons",
      "population": 18000,
      "before_accessibility": 82.7,
      "after_accessibility": 18.2,
      "accessibility_drop": 64.5,
      "before_classification": "Well Served",
      "after_classification": "Critical Desert",
      "was_nearest_service": true,
      "became_underserved": true
    }
  ]
}
```

##### `GET /decision/failure-simulation`
- **Description:** GET endpoint for facility failure simulation.
- **Query Parameters:** `service_id` (required int), `scope` (optional string, default: "city").

##### `POST /decision/future-risk`
- **Description:** Calculates deterministic forward-looking civic risk projections under configurable population demand growth. Explicitly labeled as a demo estimate.
- **Request Body:**
```json
{
  "growth_rate_pct": 15.0,
  "time_horizon_years": 5,
  "service_type": "healthcare",
  "area_id": null
}
```
- **Response `200 OK`**:
```json
{
  "service_type": "healthcare",
  "growth_rate_pct": 15.0,
  "time_horizon_years": 5,
  "evaluated_areas_count": 5,
  "current_risk_score": 57.4,
  "projected_risk_score": 61.2,
  "risk_increase": 3.8,
  "current_risk_category": "High Risk",
  "projected_risk_category": "High Risk",
  "risk_trend": "Growing Pressure",
  "areas_at_risk": [
    {
      "area_id": 9,
      "area_name": "Highlands Valley",
      "current_population": 22000,
      "projected_population": 25300,
      "current_risk_score": 92.1,
      "projected_risk_score": 92.8,
      "risk_increase": 0.7,
      "current_risk_category": "Critical Risk",
      "projected_risk_category": "Critical Risk",
      "capacity_status": "Critical",
      "primary_vulnerability": "No existing Healthcare facility in catchment"
    }
  ],
  "vulnerability_factors": [
    "15.0% population demand expansion over 5-year planning horizon",
    "Depletion of municipal capacity headroom in high-density corridors",
    "Compounding risk in unserviced peripheral neighbourhoods"
  ],
  "is_demo_estimate": true,
  "label": "Demo Estimate - Deterministic Future Risk Foundation",
  "disclaimer": "Demo estimate for strategic planning only. Projections model uniform 15.0% population demand increase over 5 years without compensatory facility additions."
}
```

##### `GET /decision/future-risk`
- **Description:** GET endpoint for future risk estimation.
- **Query Parameters:** `growth_rate_pct` (optional float, default: 15.0), `time_horizon_years` (optional int, default: 5), `service_type` (optional string), `area_id` (optional int).

---

#### 10. Community Reports & Civic Trust (Stage 7)

Backend workflows for community-submitted civic service reports, server-side RBAC verification, and transparent civic trust tracking.

##### `POST /reports`
- **Description:** Submits a community report for a civic service issue or observation.
- **Authentication:** Required (Bearer token: `citizen`, `community`, `authority`, `admin`).
- **Initial Status:** Sets `status` to `PENDING_REVIEW` and `verification_status` to `PENDING_REVIEW`. Logs initial transition (`SUBMITTED` -> `PENDING_REVIEW`) into immutable audit log.
- **Request Body:**
```json
{
  "title": "Severe water leakage near Central Market",
  "description": "Main pipeline broken, large pool of clean water overflowing onto roadway.",
  "category_code": "water",
  "service_id": null,
  "area_id": null,
  "latitude": 12.9750,
  "longitude": 77.5950,
  "severity": "high",
  "evidence_metadata": {
    "has_photo": true,
    "sensor_telemetry": { "flow_anomaly": true }
  }
}
```
- **Response `201 Created`**:
```json
{
  "id": 1,
  "reporter_id": "1",
  "category_id": 4,
  "category_code": "water",
  "service_id": null,
  "service_name": null,
  "area_id": 1,
  "area_name": "Central Ward",
  "title": "Severe water leakage near Central Market",
  "description": "Main pipeline broken, large pool of clean water overflowing onto roadway.",
  "latitude": 12.9750,
  "longitude": 77.5950,
  "severity": "high",
  "status": "PENDING_REVIEW",
  "verification_status": "PENDING_REVIEW",
  "confidence_score": 0.55,
  "source_type": "community",
  "created_at": "2026-10-09T02:30:00Z",
  "updated_at": "2026-10-09T02:30:00Z",
  "evidence_metadata": {
    "has_photo": true,
    "sensor_telemetry": { "flow_anomaly": true }
  }
}
```

##### `GET /reports`
- **Description:** Lists cataloged community reports with optional filtering.
- **Query Parameters:**
  - `status` (optional string): e.g. `PENDING_REVIEW`, `COMMUNITY_VERIFIED`, `OFFICIAL`, `REJECTED`
  - `verification_status` (optional string)
  - `category_code` (optional string): e.g. `water`, `healthcare`, `transport`
  - `area_id` (optional int)
  - `service_id` (optional int)
  - `limit` (optional int, default: `50`, max: `200`)
  - `offset` (optional int, default: `0`)
- **Response `200 OK`**: `List[ReportResponse]`

##### `GET /reports/{report_id}`
- **Description:** Retrieves detailed community report including full verification history and immutable audit trail.
- **Response `200 OK`**:
```json
{
  "id": 1,
  "reporter_id": "1",
  "category_id": 4,
  "category_code": "water",
  "service_id": null,
  "service_name": null,
  "area_id": 1,
  "area_name": "Central Ward",
  "title": "Severe water leakage near Central Market",
  "description": "Main pipeline broken, large pool of clean water overflowing onto roadway.",
  "latitude": 12.9750,
  "longitude": 77.5950,
  "severity": "high",
  "status": "OFFICIAL",
  "verification_status": "OFFICIAL",
  "confidence_score": 1.0,
  "source_type": "community",
  "created_at": "2026-10-09T02:30:00Z",
  "updated_at": "2026-10-09T02:35:00Z",
  "evidence_metadata": null,
  "verifications": [
    {
      "id": 1,
      "verifier_id": "2",
      "verification_status": "COMMUNITY_VERIFIED",
      "verification_type": "peer_confirmation",
      "notes": "Verified by community patrol group.",
      "created_at": "2026-10-09T02:32:00Z"
    },
    {
      "id": 2,
      "verifier_id": "3",
      "verification_status": "OFFICIAL",
      "verification_type": "official_audit",
      "notes": "Official municipal work order issued #WO-8821.",
      "created_at": "2026-10-09T02:35:00Z"
    }
  ],
  "audit_trail": [
    {
      "id": 1,
      "actor_id": "1",
      "action": "create",
      "entity_type": "community_report",
      "entity_id": 1,
      "previous_value": "SUBMITTED",
      "new_value": "PENDING_REVIEW",
      "reason": "Initial community report submitted: Severe water leakage near Central Market",
      "created_at": "2026-10-09T02:30:00Z"
    },
    {
      "id": 2,
      "actor_id": "2",
      "action": "status_change",
      "entity_type": "community_report",
      "entity_id": 1,
      "previous_value": "PENDING_REVIEW",
      "new_value": "COMMUNITY_VERIFIED",
      "reason": "Verified by community patrol group.",
      "created_at": "2026-10-09T02:32:00Z"
    },
    {
      "id": 3,
      "actor_id": "3",
      "action": "status_change",
      "entity_type": "community_report",
      "entity_id": 1,
      "previous_value": "COMMUNITY_VERIFIED",
      "new_value": "OFFICIAL",
      "reason": "Official municipal work order issued #WO-8821.",
      "created_at": "2026-10-09T02:35:00Z"
    }
  ]
}
```

##### `POST /reports/{report_id}/verify`
- **Description:** Verifies, updates status, or rejects a community report.
- **Server-Side RBAC Enforcement:**
  - `COMMUNITY_VERIFIED`: Allowed for `community`, `authority`, `admin` roles.
  - `AUTHORITY_VERIFIED`: Allowed for `authority`, `admin` roles (returns `403` for `citizen` / `community`).
  - `OFFICIAL`: Allowed for `authority`, `admin` roles (returns `403` for `citizen` / `community`).
  - `REJECTED`: Allowed for `authority`, `admin` roles (returns `403` for `citizen` / `community`).
- **Request Body:**
```json
{
  "verification_status": "OFFICIAL",
  "notes": "Verified on-site and integrated into official city repair schedule."
}
```
- **Response `200 OK`**: `ReportDetailResponse`

##### `GET /reports/{report_id}/audit-trail`
- **Description:** Returns the immutable audit trail for a report.
- **Response `200 OK`**: `List[AuditLogItem]`


