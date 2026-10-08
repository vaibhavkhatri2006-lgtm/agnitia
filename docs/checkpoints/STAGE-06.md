# Stage 6 Checkpoint — Map + Core Dashboard Backend

## Objective
Provide the backend APIs and geospatial data required for Person 1's map and core dashboard. Enable the frontend to retrieve administrative locality boundaries and GeoJSON polygon outlines, civic facility Point marker GeoJSON, composite and per-category accessibility/gap scores, underserved rankings leaderboard, and comprehensive selected-area metrics without duplicate analytics calculations.

---

## Implemented

1. **Locality Polygon GeoJSON Layer**:
   - `GET /areas/geojson`: Returns an RFC 7946 GeoJSON `FeatureCollection` of administrative areas, wards, and neighbourhoods.
   - `GET /areas/{area_id}/geojson`: Returns an RFC 7946 GeoJSON `Feature` for an individual locality.
   - Shapely WKT parsing guarantees valid WGS84 CRS coordinate structures for Leaflet/MapLibre polygon rendering.
   - Built-in analytics enrichment embeds `accessibility_score`, `gap_score`, and `desert_classification` directly in feature properties.

2. **Civic Facility Point Marker GeoJSON Layer**:
   - `GET /services/geojson`: Returns RFC 7946 Point `FeatureCollection` for facilities with coordinates `[longitude, latitude]`.
   - Supports frontend filtering by `category_code`, `area_id`, and `status`.

3. **Underserved Rankings Leaderboard**:
   - `GET /analytics/rankings/underserved`: Generates prioritized rankings of areas ordered by severity of service gaps.
   - Supports both composite multi-category scan and single-category scans (healthcare, education, transport, water, market).
   - Stable deterministic tie-breaking (`-gap_score`, `-population`, `area_id`).

4. **Selected Area Core Dashboard Scorecard**:
   - `GET /analytics/areas/{area_id}` delivers complete metric payloads for the dashboard scorecard:
     - Accessibility Score
     - Gap Score
     - Service Desert Classification
     - Population
     - Nearest facility name, distance (km), and estimated travel time (min)
     - Capacity, load, and service pressure category
     - Equity score
     - Data confidence score
     - Community ground-report Reality Gap metrics

5. **Fault-Tolerant & Empty Data Handling**:
   - Graceful null geometry fallbacks conforming to RFC 7946 (`geometry: null`).
   - Clean empty collections for unmatched filters without exceptions.

---

## APIs

- `GET /areas/geojson`
- `GET /areas/{area_id}/geojson`
- `GET /services/geojson`
- `GET /analytics/rankings/underserved`
- `GET /areas`
- `GET /areas/{area_id}`
- `GET /services`
- `GET /services/{service_id}`
- `GET /services/categories`
- `GET /analytics/areas`
- `GET /analytics/areas/{area_id}`
- `GET /analytics/areas/{area_id}/category/{category_code}`
- `GET /analytics/deserts`

---

## Checks

| Check | Expected | Result |
| :--- | :--- | :--- |
| **Map / Locality API** | `/areas` and `/areas/{id}` return administrative areas | **PASS** |
| **Service API** | `/services`, `/services/{id}`, `/services/categories` functional | **PASS** |
| **GeoJSON Validation** | Area polygons and service points comply with RFC 7946 WGS84 | **PASS** |
| **Accessibility / Gap API** | Verified composite & category accessibility/gap scores | **PASS** |
| **Ranking API** | `/analytics/rankings/underserved` returns sorted leaderboard | **PASS** |
| **Selected-Area Metrics** | All scorecard metrics returned for UI display | **PASS** |
| **Empty Data Handling** | Filter mismatches return safe empty collections without error | **PASS** |
| **Stage 3 Regression** | All Stage 3 analytics tests pass | **PASS** (14/14) |
| **Stage 4 Regression** | All Stage 4 candidate, recommendation, simulation, investment tests pass | **PASS** (51/51) |
| **Backend Startup** | Health check probe passes with healthy status | **PASS** |

---

## Result
**PASS**

---

## Known Issues / Limitations
- Vector tile caching (Mapbox Vector Tiles) and real-time streaming sockets deferred to later stages.
- No frontend code was modified; Person 1 can integrate map and dashboard directly using documented endpoints.

---

## Next Stage
**STAGE 7**
