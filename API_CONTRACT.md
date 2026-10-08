# CivicPulse API Contract

## Version: 0.2.0
## Stage: Stage 2 (Backend Core + Auth)

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
