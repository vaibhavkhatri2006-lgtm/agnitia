# Stage 01 Checkpoint

## Objective
Establish the complete database foundation, schema migration lifecycle with Alembic, SQLAlchemy 2.0 ORM models, and deterministic demo dataset for CivicPulse as Person 2 (Backend / Database / GIS / AI).

---

## Implemented
1. **Database Schema & Models**:
   - Engineered 9 core relational and spatial models supporting geographic hierarchy, services, categories, capacities, demographic population cells, community reporting, verification audits, data sources, and audit logs.
   - Built a custom `SafeGeometry` TypeDecorator supporting PostgreSQL/PostGIS native geometries and indexes while gracefully supporting SQLite development and Shapely geometric validation.
2. **Alembic Migration Pipeline**:
   - Initialized Alembic configuration with dynamic connection string mapping to `app.config.settings`.
   - Generated and tested migration version `faafc5ad4477_create_stage_1_tables.py`.
   - Verified bidirectional schema migration lifecycle: `alembic upgrade head` and `alembic downgrade base`.
3. **Deterministic Demo Data Seed**:
   - Authored `backend/seed.py` providing reproducible, deterministic urban data labeled `simulated_demo`.
   - Included geographic hierarchy (City -> Wards -> Neighbourhoods), healthcare deserts (Highlands Valley), transit disruptions (South Hillside Bus Hub), overcrowded facilities, community reports, and verification histories.
4. **Automated Verification & Test Suite**:
   - Authored `backend/tests/test_database.py` with 7 thorough test cases covering foreign-key constraints, uniqueness, geometry validity via Shapely, and sample analytical queries.
   - Authored `backend/verify_stage1.py` standalone end-to-end verification script.

---

## Database Tables
1. `geographic_areas`: Hierarchical administrative areas with SRID 4326 geometries and population metrics.
2. `service_categories`: Data-driven service taxonomy (healthcare, education, transport, water, market).
3. `services`: Civic service infrastructure facilities with coordinates, geometries, and operational statuses.
4. `population_cells`: Granular demographic population cells with geometry boundaries and demographic ratios.
5. `service_capacities`: Capacity limits, current loads, and constraint statuses per service.
6. `community_reports`: Geo-tagged citizen reports with severity levels, category/service references, and status tracking.
7. `report_verifications`: Audit records of report verifications with notes, types, and statuses.
8. `data_sources`: Registry of data provenance and trust scores (`simulated_demo`, `osm`, `government`, `community`, `admin`).
9. `audit_logs`: System mutation and action history.

---

## Demo Data
- **Data Sources**: 5 records (trust levels 0.70 to 1.00)
- **Service Categories**: 5 records (healthcare, education, transport, water, market)
- **Geographic Areas**: 10 records across 3 hierarchical levels:
  - 1 City: Metro City (Pop 72,000)
  - 4 Wards: Central Ward, Riverside North, Highlands East, Southern Outskirts
  - 5 Neighbourhoods: Downtown Core, West End, Riverside Commons, Highlands Valley, South Hillside
- **Population Cells**: 4 granular cells with demographic JSON breakdowns
- **Services & Capacities**: 14 facilities with varying operational and capacity conditions
- **Community Reports**: 4 geo-located citizen reports (including critical transport and high water reports)
- **Report Verifications**: 2 verification audit entries
- **Audit Logs**: 1 seed audit record

---

## Files Changed
- `backend/requirements.txt`
- `backend/alembic.ini`
- `alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/faafc5ad4477_create_stage_1_tables.py`
- `backend/app/models/types.py`
- `backend/app/models/data_source.py`
- `backend/app/models/geographic_area.py`
- `backend/app/models/service_category.py`
- `backend/app/models/service.py`
- `backend/app/models/service_capacity.py`
- `backend/app/models/population_cell.py`
- `backend/app/models/community_report.py`
- `backend/app/models/report_verification.py`
- `backend/app/models/audit_log.py`
- `backend/app/models/__init__.py`
- `backend/seed.py`
- `backend/verify_stage1.py`
- `backend/tests/test_database.py`
- `README.md`
- `BUILD_STATE.md`
- `docs/checkpoints/STAGE-01.md`

---

## Commands Run
- `alembic revision --autogenerate -m "create_stage_1_tables"`
- `backend\.venv\Scripts\alembic.exe upgrade head`
- `backend\.venv\Scripts\alembic.exe downgrade base`
- `backend\.venv\Scripts\alembic.exe upgrade head`
- `backend\.venv\Scripts\python.exe backend\seed.py`
- `backend\.venv\Scripts\pytest.exe backend\tests`
- `backend\.venv\Scripts\python.exe backend\verify_stage1.py`

---

## Checks
1. migration up — **PASS**
2. migration down/reapply — **PASS**
3. seed — **PASS**
4. DB integrity tests — **PASS**
5. geometry validity — **PASS**
6. sample queries — **PASS**

---

## Result
**PASS**

---

## Known Issues
- Local development host lacks Docker and PostGIS engine binaries; SQLite with Shapely is utilized for local development while dialect-aware DDL remains fully compatible with PostgreSQL/PostGIS.

---

## Important Decisions
- Implemented `SafeGeometry` to provide PostGIS DDL on PostgreSQL while avoiding native C extension compilation issues on standard Python SQLite environments.
- Kept demo data strictly deterministic with idempotent upsert queries.
- Ensured category logic is completely data-driven and not hardcoded into table definitions.

---

## Next Stage
**Stage 2** (Civic Infrastructure & Core API Service Layer)
