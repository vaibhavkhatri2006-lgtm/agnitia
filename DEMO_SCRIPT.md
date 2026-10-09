# CivicPulse — 3-Minute Hackathon Demo Script

This script provides a structured, high-impact walkthrough for judges and presentation audiences.

---

## Part 1: Problem Hook & Overview (0:00 – 0:30)

> *"Judges, urban inequality isn't just about income—it's about access. In every growing city, vulnerable neighbourhoods become 'service deserts,' where accessing a clinic, clean water, or transport takes an hour or more. 
> 
> Planners often make multi-million dollar infrastructure decisions using gut feeling or static spreadsheets, while citizen complaints remain disconnected from planning decisions.
> 
> We built **CivicPulse**—an urban accessibility, simulation, and community analytics platform that bridges top-down municipal planning with bottom-up citizen reality."*

---

## Part 2: Map & Locality Service Gap (0:30 – 1:00)

**Action**: Open the dashboard (`http://127.0.0.1:5173`) and view the interactive map.

> *"Here on the CivicPulse map, we see the city's administrative boundaries and all cataloged facilities across 5 critical domains: healthcare, education, transport, water, and food markets.
> 
> When we click on **Highlands Valley**, our deterministic analytics engine immediately evaluates a multi-dimensional scorecard. Notice:
> - **Accessibility Score**: 13.1 out of 100
> - **Gap Score**: 86.9 (Critical Desert)
> - **Nearest Healthcare Facility**: 7.8 km away, representing an estimated 60-minute travel time.
> 
> The platform also flags a **Reality Gap**, warning planners that active community ground reports indicate severe service distress."*

---

## Part 3: Planner Command Center & Recommendation (1:00 – 1:40)

**Action**: Log in as Municipal Authority (`authority@example.com` / `Authority123!`) and open the Planner Command Center.

> *"Logging in as a Municipal Authority unlocks the Planner Command Center. The leaderboard instantly ranks the city's most underserved areas, placing Highlands Valley at Rank #1.
> 
> Instead of guessing where to build, the planner clicks **Generate Recommendations**. 
> 
> Our spatial allocation engine evaluates optimal candidate placement using centroid, population density, and gap-perimeter strategies. It scores each candidate across 7 explainable factors: gap severity, population scale, travel need, capacity pressure, and demographic equity.
> 
> The top recommendation is candidate `cand-healthcare-9-centroid` with an explainability breakdown explaining exactly why this location maximizes civic return."*

---

## Part 4: What-If Simulation & Measured Impact (1:40 – 2:20)

**Action**: Click **Run Simulation** on the recommended candidate location.

> *"Now comes the core innovation: the **What-If Simulation Lab**. 
> 
> Before committing taxpayer capital, the planner simulates building a community health center at this exact candidate location. 
> 
> In a fraction of a second, the engine evaluates the intervention in-memory:
> - **Locality Accessibility**: Jumps from 13.1 to 78.8 (+65.7 points)!
> - **Citywide Coverage**: Expands by +23.9 percentage points.
> - **Underserved Population Relieved**: 22,000 residents transitioned out of a critical healthcare desert!
> - **Travel Time**: Drops from 60 minutes to just 2.1 minutes!
> 
> And critically, this simulation is completely ephemeral—zero permanent database writes occur, allowing planners to test dozens of scenarios risk-free."*

---

## Part 5: Community Verification & Real Data Mode (2:20 – 3:00)

**Action**: Show citizen report verification and toggle Real Data Mode.

> *"CivicPulse also closes the loop with citizens:
> - A resident can report a broken water tap or closed dispensary.
> - Community members verify it locally.
> - Municipal authorities confirm it as **Official**, elevating trust to 100% with an immutable audit log.
> 
> Finally, while our Demo Mode operates 100% offline for reliable demos, CivicPulse features a **Real Data Mode**. 
> 
> With a single toggle, we can query the live OpenStreetMap Overpass API for any global locality, validate coordinates, deduplicate nearby facilities within 15 meters, and preserve documented census population data without ever fabricating numbers.
> 
> With 157 passing automated tests and mathematical determinism, CivicPulse makes urban planning transparent, equitable, and data-driven. Thank you!"*
