# CivicPulse — Project Compendium & Judges' Technical Defense Guide

> **Official Hackathon Technical Guide, System Architecture Blueprint & Defense Cheat Sheet**  
> *Target Audience: Municipal Authorities, Urban Planners, Hackathon Judges & Development Team*

---

## Quick Navigation
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [System Architecture & Full-Stack Blueprint](#2-system-architecture--full-stack-blueprint)
3. [Core Geospatial & Analytical Engines](#3-core-geospatial--analytical-engines)
4. [Spatial Decision Engine & Recommendation System](#4-spatial-decision-engine--recommendation-system)
5. [In-Memory What-If Simulation Lab & Resilience](#5-in-memory-what-if-simulation-lab--resilience)
6. [Community Ground Truth & Civic Trust Hierarchy](#6-community-ground-truth--civic-trust-hierarchy)
7. [Dual Operational Modes & OpenStreetMap Ingestion](#7-dual-operational-modes--openstreetmap-ingestion)
8. [Step-by-Step 3-Minute Live Hackathon Demo Walkthrough](#8-step-by-step-3-minute-live-hackathon-demo-walkthrough)
9. [Judges' Technical Q&A & Defense Cheat Sheet](#9-judges-technical-qa--defense-cheat-sheet)
10. [Verification, Credentials & Presentation Checklist](#10-verification-credentials--presentation-checklist)

---

## 1. Executive Summary & Problem Statement

### The Core Problem
In rapidly expanding urban centers, essential civic amenities—primary healthcare clinics, schools, potable water access points, public transit hubs, and essential food markets—are distributed unequally. Vulnerable populations frequently inhabit **service deserts**, where reaching basic healthcare requires upwards of 45–60 minutes of difficult transit.

Concurrently, municipal authorities and urban planners allocate multi-million dollar infrastructure budgets using static census spreadsheets, political intuition, or subjective guesswork. Meanwhile, real-world infrastructure failures reported by citizens (broken water pumps, flooded roads, unstaffed clinics) remain trapped in disconnected complaint databases, completely ignored by city planners.

### The Solution: CivicPulse
**CivicPulse** is an open-standard, mathematically grounded urban spatial intelligence platform that bridges top-down municipal planning with bottom-up citizen reality. Rather than relying on opaque, non-reproducible deep-learning models, CivicPulse delivers:

1. **Deterministic Multi-Criteria Analytics**: Synthesizes travel time, facility capacity load, transit connectivity, and demographic vulnerability into reproducible 0–100 accessibility and service desert scores.
2. **Algorithmic Candidate Allocation**: Identifies optimal intervention locations using geometric centroid, population density, and gap-perimeter strategies with natural language audit justifications.
3. **In-Memory What-If Simulation Lab**: Allows planners to test capital interventions before spending tax dollars. Evaluates coverage gains, accessibility jumps, and travel time savings with **zero database writes**.
4. **Verified Civic Trust Hierarchy**: Measures the *Reality Gap* by channeling citizen-reported infrastructure failures through a multi-tier, role-guarded verification pipeline from community review to official confirmation.

---

## 2. System Architecture & Full-Stack Blueprint

CivicPulse is engineered with a decoupled, clean micro-architecture:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER (Frontend)                       │
│  React 19 • TypeScript • Vite • Tailwind CSS v4 • Lucide Icons • Recharts │
│  Leaflet Map Container + OpenStreetMap Tiles (Free, Zero API Key Required)│
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ REST / JSON & GeoJSON (RFC 7946)
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION ENGINE (FastAPI)                        │
│  ├── Auth & RBAC (Citizen, Community, Authority, Admin - HS256 JWT)       │
│  ├── Geospatial & Analytics Engine (Haversine Detour, Capacity Ratios)   │
│  ├── Spatial Decision Engine (Centroid, Population Density, Perimeter)   │
│  ├── Recommendation Scoring Engine (7-Factor Normalized Weights)          │
│  ├── In-Memory What-If Simulator (Ephemeral ORM, Zero DB Writes)          │
│  ├── Systemic Resilience Engine (Outage Modeling & Single Point of Failure│
│  ├── Multi-Scale Hierarchy Service (Local, Neighbourhood, Ward, City)     │
│  ├── Community Trust & Moderation (Multi-Tier Verification & Audit Logs)  │
│  └── OpenStreetMap Ingestion (Overpass QL, 15m Deduplication, Caching)    │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ SQLAlchemy 2.0 ORM / GeoAlchemy2
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          DATA PERSISTENCE LAYER                           │
│  SQLite + Shapely (Local Dev & Testing) / PostgreSQL + PostGIS (Docker)   │
│  SRID 4326 Geometries: Point, Polygon, MultiPolygon • Alembic Migrations  │
└───────────────────────────────────────────────────────────────────────────┘
```

### Full-Stack Component Overview

| Layer | Technology | Key Capabilities & Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.12, FastAPI, Pydantic v2 | High-throughput asynchronous ASGI engine, strict type contracts, auto-generated OpenAPI 3.1 docs. |
| **Spatial Engine** | SQLAlchemy 2.0, GeoAlchemy2, Shapely | SRID 4326 WGS84 geometries, polygon containment, centroid computation, spatial deduplication. |
| **Database** | SQLite + Spatial Functions / PostGIS | Zero-dependency local execution; production-ready containerized PostGIS spatial GiST indexing. |
| **Frontend UI** | React 19, TypeScript, Vite, Tailwind v4 | Sub-second production compilation (1.5s), responsive civic-tech interface, accessible design system. |
| **Mapping Engine** | React-Leaflet, Leaflet 1.9, OpenStreetMap | 100% free tiles (zero API key), custom SVG divIcon markers, GeoJSON choropleth layers, popups. |
| **Security & RBAC** | OAuth2 Password Bearer, JWT, bcrypt | Stateless HS256 tokens, 12-round salted hashing, strict role permissions enforced on all endpoints. |

---

## 3. Core Geospatial & Analytical Engines

### A. Composite Accessibility Score Formula
Rather than naive circular buffers, CivicPulse evaluates access across five calibrated dimensions:

$$\text{Accessibility Score} = 0.30 \times S_{\text{travel}} + 0.20 \times S_{\text{avail}} + 0.20 \times S_{\text{capacity}} + 0.15 \times S_{\text{conn}} + 0.15 \times S_{\text{equity}}$$

$$\text{Gap Score} = 100.0 - \text{Accessibility Score}$$

1. **Travel Time ($S_{\text{travel}}$, 30%)**: Detour-modeled network transit/walking speeds mapped against access thresholds. Decays from 100 (instant access) to 0 (>45 mins).
2. **Service Availability ($S_{\text{avail}}$, 20%)**: Operational status of target facilities:
   - `operational` = 100
   - `limited` = 60
   - `degraded` = 50
   - `temporarily_unavailable` = 20
   - `closed` = 0
3. **Capacity Pressure ($S_{\text{capacity}}$, 20%)**: Demographic demand versus nominal facility throughput ($D/C$ ratio):
   - Low Pressure ($< 0.7$): Score = 100
   - Moderate Pressure ($0.7 - 1.0$): Score = 75
   - High Pressure ($1.0 - 1.5$): Score = 40
   - Critical Overcrowding ($> 1.5$): Score = 10
4. **Transport Connectivity ($S_{\text{conn}}$, 15%)**: Multimodal proximity to transit nodes (metro station, bus terminals) within 400m.
5. **Demographic Equity ($S_{\text{equity}}$, 15%)**: Prioritization of vulnerable populations based on dependency ratios and poverty indices.

### B. Service Desert Classifications

| Accessibility Score | Gap Score | Classification | Map Color | Description & Planning Action |
| :---: | :---: | :---: | :---: | :--- |
| **80 – 100** | $0 - 20$ | **Well Served** | Emerald Green | Optimal coverage; facilities well within standard travel times. |
| **60 – 79** | $20 - 40$ | **Adequate** | Yellow | Acceptable baseline; vulnerable to seasonal demand spikes. |
| **40 – 59** | $40 - 60$ | **At Risk / Underserved** | Amber / Orange | Emerging service deficit; travel times exceed 25 minutes. |
| **20 – 39** | $60 - 80$ | **Underserved** | Deep Orange | Acute infrastructure deficit; high priority for capital funding. |
| **0 – 19** | $80 - 100$ | **Critical Desert** | Crimson Red | Complete civic deprivation; zero reachable operational facilities. |

### C. Pluggable Routing Engine
- **Deterministic Urban Detour Model (Default / Offline)**: Scaled Haversine distance ($1.30\times$ street grid factor) running 100% offline at sub-millisecond latency.
- **OSRM (Open Source Routing Machine)**: Live road network routing engine enabled via `USE_OSRM=True`, with automatic fallback to deterministic detour if unavailable.

---

## 4. Spatial Decision Engine & Recommendation System

### A. Algorithmic Candidate Location Allocation
When an area is identified as a service desert, the system algorithmically generates candidate sites using three geometric strategies:

1. **Geometric Centroid**: Mathematical center of gravity of the underserved polygon computed using Shapely.
2. **Population Density Node**: Highest-density population cell centroid within the neighbourhood boundary to maximize 15-minute walking catchment.
3. **Gap Perimeter Node**: Interior point furthest from all existing facilities to eliminate geographic blind spots.

*Validation:* Every candidate is verified for strict geometric containment inside the boundary (`polygon.contains(pt)`) and spatially deduplicated within an 11-meter tolerance.

### B. 7-Factor Normalized Recommendation Scoring
$$\text{Score} = 0.30 \times \text{Gap} + 0.25 \times \text{Pop} + 0.15 \times \text{Travel} + 0.10 \times \text{Capacity} + 0.10 \times \text{Equity} + 0.05 \times \text{Connectivity} + 0.05 \times \text{Confidence}$$

- **Gap Severity (30%)**: Prioritizes areas with highest baseline deficits.
- **Population Scale (25%)**: Maximizes absolute civic return on investment.
- **Travel Deficit (15%)**: Targets areas with excessive transit burdens.
- **Capacity Pressure (10%)**: Relieves overburdened facilities in adjacent areas.
- **Demographic Equity (10%)**: Targets socio-economically marginalized zones.
- **Transport Connectivity (5%)**: Prefers sites with strong regional transit links.
- **Data Confidence (5%)**: Weights decisions by empirical verification levels.

### C. Natural Language Explainability (XAI)
Every recommendation generates human-readable justification strings:
> *"Ranked #1 (Score: 80.6) because of severe healthcare accessibility gap (86.9%) in Highlands Valley, large affected population (22,000 residents), long estimated travel time with no reachable facility in catchment, and strong transit connectivity supporting regional catchment."*

---

## 5. In-Memory What-If Simulation Lab & Resilience

### Ephemeral In-Memory ORM Architecture
The simulation engine runs **100% in-memory**:
- Proposed facilities are instantiated as ephemeral SQLAlchemy ORM objects.
- Dynamically blended into catchment queries alongside official records.
- **Zero database writes (`session.commit()`) occur**, guaranteeing zero database corruption or schema mutation.

### Measured Impact Example: Highlands Valley

| Metric | Baseline State | Post-Simulation State | Measured Civic Gain |
| :--- | :---: | :---: | :---: |
| **Locality Accessibility** | 13.1 / 100 (Critical Desert) | 78.8 / 100 (Well Served) | **+65.7 Points** |
| **Citywide Healthcare Coverage** | 68.2% | 92.1% | **+23.9% Expansion** |
| **Underserved Residents** | 22,000 residents | 0 residents | **22,000 Residents Relieved** |
| **Average Commute Time** | 60.0 mins (transit) | 2.1 mins (walk) | **57.9 Minutes Saved / Trip** |

### Systemic Resilience & Single Point of Failure (SPOF) Analysis
CivicPulse can model the catastrophic failure or outage of any existing facility. It computes the resulting coverage loss, accessibility drop, and newly underserved population, flagging whether the facility constitutes a **Single Point of Failure (SPOF)**.

---

## 6. Community Ground Truth & Civic Trust Hierarchy

### Multi-Tier Verification Lifecycle
```
[ Citizen Submission ]
          │
          ▼
   SUBMITTED (Confidence: 0.50)
          │
          ▼
   PENDING_REVIEW (Awaiting community ground check)
          │
   ┌──────┴────────────────────────┐
   ▼                               ▼
COMMUNITY_VERIFIED           REJECTED (Confidence: 0.00)
(Peer verified: 0.75 - 0.90)        (Flagged as false/spam)
   │
   ▼
AUTHORITY_VERIFIED (Municipal official confirmed: 0.95)
   │
   ▼
OFFICIAL (Legally binding municipal status: 1.00)
```

### Server-Side Role-Based Access Control (RBAC)

| Role | System Permissions | Verification Authority |
| :--- | :--- | :--- |
| `citizen` | Public read (`data:read`), submit reports (`report:create`). | Cannot verify reports (Attempts return HTTP 403 Forbidden). |
| `community` | Citizen permissions + peer verification (`report:verify_community`). | Can perform peer verification up to `COMMUNITY_VERIFIED`. |
| `authority` | Municipal operations (`authority:operate`) + official audit (`report:verify_official`). | Approves `OFFICIAL` status or marks reports as `REJECTED`. |
| `admin` | Full administrative control (`admin:manage`), system audit oversight. | Complete administrative moderation across all system states. |

---

## 7. Dual Operational Modes & OpenStreetMap Ingestion

### DEMO MODE (Default & Offline)
- Self-contained deterministic seed dataset of "Metro City" (Bangalore coordinates).
- 10 administrative areas, 14 verified facilities across 5 categories, 50 community reports.
- Operates 100% offline without API keys or external network dependencies.
- Guarantees zero presentation flakiness during hackathon demos.

### REAL DATA MODE (Live Global GIS)
- Queries OpenStreetMap via live Overpass QL API for any global municipality.
- Extracts 5 core service categories: Healthcare, Education, Transport, Water, Markets.
- Anti-Null Island coordinate sanitizer (rejects 0,0 or out-of-bound coordinates).
- 15-meter spatial deduplication buffer against existing database records.
- SHA256 query caching with 24-hour TTL and 1.0s query cooldown rate-limiting.

### Strict Population Data Integrity Rule
When ingesting real-world geographic data, CivicPulse **never invents, hallucinates, or synthesizes census population figures**. If documented public census data is provided, it is stored as `population_status="documented"`. If census records are unavailable, the count is recorded as `None` with `population_status="unavailable"`, and downstream capacity formulas adapt gracefully with explicit data quality notices.

---

## 8. Step-by-Step 3-Minute Live Hackathon Demo Walkthrough

### Part 1: Problem Hook (0:00 – 0:30)
> *"Judges, urban inequality isn't just about income—it's about access. In every growing city, vulnerable neighbourhoods become service deserts where reaching a clinic takes an hour or more. Planners make multi-million dollar capital decisions using static spreadsheets, while citizen reports remain ignored. We built CivicPulse to bridge top-down municipal planning with bottom-up citizen reality."*

### Part 2: Interactive Map & Locality Service Gap (0:30 – 1:00)
- **Action**: Open `http://127.0.0.1:5173/map`. Point out OpenStreetMap tiles and custom color-coded category markers. Click on the **Highlands Valley** polygon.
> *"On the CivicPulse map, we see the city's administrative boundaries and cataloged facilities across healthcare, education, transport, water, and food markets. Clicking Highlands Valley reveals a critical healthcare gap: Accessibility Score is 13.1 / 100, Gap is 86.9, and the nearest clinic is 7.8 km away, representing an estimated 60-minute travel time."*

### Part 3: Planner Command Center & Recommendations (1:00 – 1:40)
- **Action**: Log in as Municipal Authority (`authority@example.com` / `Authority123!`). Switch to Recommendations Layer or open Planner view.
> *"Logging in as Municipal Authority unlocks planning intelligence. The priority leaderboard instantly ranks Highlands Valley at #1. Instead of guessing where to build, we click Generate Recommendations. Our spatial engine scores candidate locations across 7 normalized criteria. Candidate cand-healthcare-9-centroid ranks #1 with clear explainable justifications."*

### Part 4: What-If Simulation Lab & Measured Impact (1:40 – 2:20)
- **Action**: Run the simulation for the top candidate.
> *"Now for our core innovation: the What-If Simulation Lab. Before spending public funds, the planner simulates building a community health center at this exact site. In milliseconds, our in-memory engine re-evaluates the city: Locality accessibility jumps from 13.1 to 78.8 (+65.7 points)! 22,000 residents are relieved from a healthcare desert! Average travel time drops from 60 minutes to 2.1 minutes! And zero database writes occurred—planners can test dozens of scenarios completely risk-free."*

### Part 5: Community Ground Truth & OpenStreetMap Toggle (2:20 – 3:00)
- **Action**: Show Community Reports layer and toggle Query OSM.
> *"Finally, CivicPulse integrates citizen ground reality. Citizens report infrastructure breakdowns; community members verify them; municipal officials approve them as Official with an immutable audit log. And with a single click on 'Query OSM', we can ingest live OpenStreetMap amenities globally with automated deduplication. CivicPulse makes urban planning transparent, equitable, and data-driven. Thank you!"*

---

## 9. Judges' Technical Q&A & Defense Cheat Sheet

### Q1: Why use deterministic scoring rather than an LLM or deep learning?
**Answer:** Municipal capital allocations involve statutory audits, legal liabilities, and public tax dollars. A city council cannot defend an infrastructure decision with an unexplainable neural network that hallucinates or produces non-reproducible outputs. CivicPulse uses mathematically verifiable formulas with exact factor weights ($0.30 \times \text{Gap} + 0.25 \times \text{Pop} + \dots$). Every score provides auditable mathematical proof.

### Q2: How do you estimate travel times without huge Google Maps API bills?
**Answer:** We built a pluggable `RoutingProvider` architecture. By default, it uses a deterministic urban detour model scaling Haversine distances by an empirical $1.30\times$ street grid factor with walking and transit speed profiles. It executes in sub-milliseconds, runs 100% offline, and costs \$0.00. For live network graphs, it integrates with open-source OSRM with automatic fallback.

### Q3: How do you prevent citizens from spamming fake reports?
**Answer:** We enforce a 4-tier verification pipeline: citizen reports enter as `PENDING_REVIEW` (confidence 0.50). Peer community review raises trust to 0.75–0.90. Only verified municipal authorities can approve `OFFICIAL` status (confidence 1.00) or reject false reports. Server-side RBAC returns HTTP 403 if unauthorized users attempt official approvals, and every action is recorded in an immutable `audit_logs` table.

### Q4: In Real Data Mode, what happens if census population data is missing? Do you synthesize it?
**Answer:** **Never.** We adhere to a strict data integrity principle: never present synthetic values as real measurements. If population data is missing, we record `population_status="unavailable"` and report capacity pressure as neutral with an explicit data quality flag. We never fabricate numbers.

### Q5: How do simulations guarantee database integrity?
**Answer:** Simulations run **entirely in-memory**. Proposed facilities are instantiated as ephemeral ORM objects in Python memory. The analytics engine blends them into catchment calculations on the fly. Zero `session.add()` or `session.commit()` calls execute, ensuring 100% database schema and data safety.

### Q6: How do you handle OpenStreetMap licensing and usage limits?
**Answer:** All Overpass data adheres to the Open Database License (ODbL 1.0). Every record stores explicit attribution, query timestamp, and raw OSM tags. Ingestion queries are hashed via SHA256 with a 24-hour TTL cache, and we enforce a 1.0s query cooldown to respect public server usage policies.

### Q7: How does the backend tech stack scale to millions of residents?
**Answer:** FastAPI runs asynchronous non-blocking request loops. On the database layer, transitioning from SQLite to PostgreSQL + PostGIS unlocks spatial GiST indexing (R-Tree indexes), enabling spatial queries across millions of coordinates in milliseconds.

### Q8: What are current limitations and future roadmap?
**Answer:** Currently, simulations evaluate single facilities or defined multi-facility lists; combinatorial optimization across hundreds of simultaneous budget permutations is computationally intensive and planned for Stage 12+. Real-time updates currently use REST polling; WebSockets are slated for live pin broadcasting.

---

## 10. Verification, Credentials & Presentation Checklist

### System Verification Metrics
- **Automated Backend Tests:** 157 / 157 Passing (100% pass rate)
- **Frontend Production Build:** `tsc -b && vite build` passes cleanly (1.51s build time)
- **Code Linting:** `oxlint` passes with 0 errors across 31 files and 116 rules
- **Backend Health Probe:** `GET /health` returns `healthy` with SQLite connected

### Demo Account Credentials

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@example.com` | `Citizen123!` | Public map exploration, report submission |
| **Community** | `community@example.com` | `Community123!` | Peer ground report verification |
| **Municipal Authority** | `authority@example.com` | `Authority123!` | Planner Command Center, Simulation Lab, Official approval |
| **Admin** | `admin@example.com` | `Admin123!` | Complete administrative moderation |

### Quick Launch Commands
- **Backend**: `backend\.venv\Scripts\python.exe backend\run.py` &rarr; `http://127.0.0.1:8000`
- **Frontend**: `cd frontend && npm.cmd run dev` &rarr; `http://127.0.0.1:5173`
- **API Docs**: `http://127.0.0.1:8000/docs`
