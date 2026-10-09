# CivicPulse — Judges' Q&A & Technical Defense

This document prepares the team to answer technical, architectural, and policy questions from hackathon judges.

---

### Q1: Why use a deterministic scoring model rather than an LLM or deep learning black-box?
**Answer**:
Urban infrastructure allocations involve millions in public funding, statutory audits, and equity obligations. Municipal decisions cannot be justified in court or city council meetings with a black-box neural network that hallucinates or produces non-reproducible outputs. 

CivicPulse uses a deterministic, mathematically verifiable multi-factor scoring model ($0.30 \times \text{Gap} + 0.25 \times \text{Population} + \dots$). Every score produces explicit factor value breakdowns and traceable reasons. When a planner asks *"Why was Location A ranked higher than Location B?"*, CivicPulse provides an exact, auditable mathematical proof.

---

### Q2: How do you estimate travel times without incurring huge Google Maps API bills?
**Answer**:
CivicPulse implements a pluggable routing provider architecture (`RoutingProvider`):
1. **Deterministic Urban Detour Model (Default / Offline)**: Uses the Haversine great-circle distance scaled by an empirical urban street grid detour coefficient ($1.30\times$) and mode-specific transit/walking speed profiles. This runs 100% offline, executes in sub-milliseconds, and is completely free.
2. **OSRM (Open Source Routing Machine)**: When configured via `USE_OSRM=True`, queries local or remote OSRM routing instances over real road networks.
3. **Graceful Fallback**: If OSRM times out or is unreachable, the system automatically falls back to the deterministic model (`provider: "fallback_deterministic"`) with an explanatory warning, ensuring the application never crashes.

---

### Q3: How do you prevent citizens from submitting fake reports or spamming the system?
**Answer**:
CivicPulse enforces a multi-tier verification and confidence scoring model:
- Citizen reports start in `PENDING_REVIEW` with baseline confidence ($0.50$).
- Community members conduct peer ground verification, boosting confidence to $0.75 - 0.90$ (`COMMUNITY_VERIFIED`).
- Only verified municipal officials (`authority` role) can promote a report to `OFFICIAL` status (confidence $1.00$) or reject it (`REJECTED`, confidence $0.00$).
- Server-side RBAC strictly prevents citizens from approving official status (returning HTTP 403 Forbidden).
- Every verification action is permanently recorded in the immutable `audit_logs` table with the actor ID, timestamp, and audit notes.

---

### Q4: In Real Data Mode, what happens if census population data is missing? Do you synthesize it?
**Answer**:
**Never.** We enforce a strict population integrity rule: **never present synthetic values as real-world measurements**.
- If a user provides a documented population from an official census or public dataset, it is recorded and flagged as `population_status="documented"`.
- If population data is missing, CivicPulse sets `population_count=None` and flags `population_status="unavailable"`.
- The analytical engine is engineered to handle zero or missing population without dividing by zero, reporting capacity pressure as neutral or unreported with explicit data quality notices.

---

### Q5: How does the What-If simulation engine work without corrupting the official database?
**Answer**:
Simulations operate **entirely in-memory**:
- Proposed facilities are instantiated as ephemeral, non-committed ORM objects in memory.
- The `AnalyticsEngine` accepts an optional `additional_services` parameter that dynamically blends simulated facilities into catchment calculations alongside official services.
- The Before vs After deltas are computed on the fly.
- Zero `session.add()` or `session.commit()` calls occur for simulation facilities, guaranteeing 100% database integrity.

---

### Q6: How do you handle OpenStreetMap data licensing and attribution?
**Answer**:
All OpenStreetMap data retrieved via our Overpass API client respects the Open Database License (ODbL 1.0):
- Every imported record stores explicit attribution (`"© OpenStreetMap contributors"`), ODbL license metadata, query endpoint URL, retrieval timestamp, and raw OSM tags.
- Data provenance can be inspected per facility via `GET /services/{id}/provenance` or `GET /osm/provenance/{id}`.
- Ingestion queries are cached using SHA256 digests with a 24-hour TTL, and we enforce a minimum 1.0-second cooldown between live queries to respect public Overpass server usage policies.

---

### Q7: What is your backend tech stack and how does it scale?
**Answer**:
- **Framework**: Python 3.12 with FastAPI and Pydantic v2 for high-throughput asynchronous request handling and strict validation.
- **ORM & GIS**: SQLAlchemy 2.0 with GeoAlchemy2 and Shapely for geometry manipulation (SRID 4326).
- **Database**: SQLite for local lightweight development, transitioning seamlessly to PostgreSQL + PostGIS via Docker Compose for production spatial indexing.
- **Security**: Stateless HS256 JWT tokens with 12-round bcrypt salted password hashing.

---

### Q8: What are the current limitations of the platform?
**Answer**:
1. **Combinatorial Multi-Facility Optimization**: Currently, what-if simulations evaluate single facilities or defined multi-facility scenarios; automated brute-force combinatorial budget optimization across hundreds of simultaneous locations is computationally intensive and planned for Stage 12+.
2. **Real-time Push Notifications**: Status changes are currently polled via REST APIs; WebSockets can be introduced for live map pin status broadcasts.
3. **Regional Demographic Interpolation**: Multi-scale analysis supports Local, Neighbourhood, Ward, and City; higher tiers (State, Country) return clean safe no-data responses until regional GIS raster datasets are ingested.
