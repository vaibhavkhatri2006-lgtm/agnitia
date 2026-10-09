# Stage 02 Checkpoint

## Objective
Establish the backend authentication core, JWT token lifecycle, server-side Role-Based Access Control (RBAC), permission dependencies, and standardized API error handling for CivicPulse as Person 2 (Backend / Database / GIS / AI).

---

## Implemented
1. **User and RBAC Schema Models**:
   - `User` model with salted bcrypt password hash, active status flag, and foreign key to `Role`.
   - `Role` model supporting `citizen`, `community`, `authority`, and `admin`.
   - `Permission` model and `role_permissions` association table for granular permission assignment.
   - Generated and tested Alembic migration `fe143b566a82_create_auth_and_rbac_tables.py`.
2. **Security & Cryptography Engine**:
   - Implemented `app.core.security` with `bcrypt` salted hashing and `PyJWT` signed token creation and decoding.
   - Configured token expiration, claims encoding (`sub`, `email`, `role`, `permissions`, `iat`, `exp`), and validation against `settings.JWT_SECRET_KEY`.
3. **Reusable Authorization Dependencies**:
   - `get_current_user`: extracts and validates bearer tokens, loading active user records.
   - `require_active_user`: rejects disabled accounts with `403 Forbidden`.
   - `require_role`: server-side guard verifying user role against permitted roles.
   - `require_permission`: server-side guard verifying required permission codes.
4. **API Router & Endpoints**:
   - `POST /auth/login`: verifies credentials, issues JWT access tokens.
   - `GET /auth/me`: returns authenticated profile and permissions.
   - `GET /auth/verify-role/authority`: role verification test for authority operations.
   - `GET /auth/verify-role/admin`: role verification test for administrative actions.
   - `GET /auth/verify-role/community`: role verification test for community verifiers.
5. **Standardized Error Handling**:
   - Registered global exception handlers for `HTTPException` (401, 403, 404), `RequestValidationError` (422), and uncaught exceptions (500) ensuring consistent JSON responses without leaking tracebacks.
6. **Deterministic Demo Accounts**:
   - Seeded reproducible demo accounts for all roles with known credentials for testing.

---

## Authentication Architecture
- **Protocol**: OAuth2 Password Bearer with JWT tokens.
- **Hashing**: `bcrypt` (12 rounds) with unique salt per user.
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Enforcement**: Strictly server-side; client claims in headers or request bodies are ignored in favor of cryptographic verification and database state.

---

## Roles
1. `citizen`: General public access; read civic data and submit civic reports.
2. `community`: Community active members; peer review and community verification.
3. `authority`: Municipal urban planners and officials; official operations and authority audits.
4. `admin`: System administrators; configuration, security, and full platform oversight.

---

## Permissions
- `data:read`: Read public infrastructure data and statistics.
- `report:create`: Submit citizen civic reports.
- `report:verify_community`: Participate in community verification reviews.
- `authority:operate`: Execute official planner operations.
- `report:verify_official`: Submit binding municipal verification.
- `admin:manage`: System administration and configuration.

---

## API Endpoints
- `POST /auth/login`
- `GET /auth/me`
- `GET /auth/verify-role/authority`
- `GET /auth/verify-role/admin`
- `GET /auth/verify-role/community`
- `GET /health`
- `GET /`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

---

## Files Changed
- `.env.example`
- `API_CONTRACT.md`
- `BUILD_STATE.md`
- `README.md`
- `docs/checkpoints/STAGE-02.md`
- `backend/.env.example`
- `backend/.env`
- `backend/requirements.txt`
- `backend/alembic/versions/fe143b566a82_create_auth_and_rbac_tables.py`
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/core/__init__.py`
- `backend/app/core/security.py`
- `backend/app/dependencies/__init__.py`
- `backend/app/dependencies/auth.py`
- `backend/app/models/__init__.py`
- `backend/app/models/role.py`
- `backend/app/models/permission.py`
- `backend/app/models/user.py`
- `backend/app/routes/__init__.py`
- `backend/app/routes/auth.py`
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/auth.py`
- `backend/app/schemas/errors.py`
- `backend/app/services/__init__.py`
- `backend/app/services/auth_service.py`
- `backend/seed.py`
- `backend/tests/test_auth.py`

---

## Commands Run
- `backend\.venv\Scripts\alembic.exe revision --autogenerate -m "create_auth_and_rbac_tables"`
- `backend\.venv\Scripts\alembic.exe upgrade head`
- `backend\.venv\Scripts\alembic.exe downgrade faafc5ad4477`
- `backend\.venv\Scripts\alembic.exe upgrade head`
- `backend\.venv\Scripts\python.exe backend\seed.py`
- `backend\.venv\Scripts\pytest.exe backend\tests`

---

## Checks
- backend unit tests — **PASS**
- login tests — **PASS**
- invalid login — **PASS**
- expired/invalid token — **PASS**
- role authorization — **PASS**
- citizen authority-action restriction — **PASS**
- authority permissions — **PASS**
- backend startup — **PASS**
- database migration — **PASS**
- OpenAPI — **PASS**
- demo login — **PASS**

---

## Result
**PASS**

---

## Known Issues
- None. All auth endpoints, RBAC dependencies, and tests pass completely.

---

## Important Decisions
- Kept RBAC validation strictly server-side through reusable FastAPI dependencies rather than checking inside route handlers.
- Integrated demo user seeding directly into the existing `backend/seed.py` deterministic script.
- Used direct `bcrypt` and `PyJWT` to ensure optimal performance, compatibility with Python 3.12, and zero deprecation warnings.

---

## Next Stage
**Stage 3** (GIS & Spatial Analytics Engine)
