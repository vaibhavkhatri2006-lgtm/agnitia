import React from 'react';
import {
  BookOpen,
  Calculator,
  Gauge,
  Clock,
  Activity,
  Users,
  Bus,
  ShieldAlert,
  Scale,
  MapPin,
  TrendingDown,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Compass,
  ArrowRight,
  Database,
} from 'lucide-react';

export const MethodologyPage = () => {
  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-10">
      {/* Header */}
      <div className="border-b border-slate-200 pb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold uppercase tracking-wider mb-3">
          <BookOpen className="w-3.5 h-3.5" />
          Technical Documentation
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight flex items-center gap-3">
          Methodology & Scoring System
        </h1>
        <p className="text-slate-600 mt-2 text-lg max-w-3xl">
          An in-depth explanation of CivicPulse&apos;s deterministic geospatial analytics, composite accessibility
          score formulas, desert classification tiers, and underlying behavioral assumptions.
        </p>
      </div>

      {/* Mission Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <Compass className="w-6 h-6 text-blue-600" />
          Why CivicPulse?
        </h2>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 text-slate-700 leading-relaxed space-y-4">
          <p>
            Urban planning in rapidly growing metropolitan hubs often suffers from an acute information disconnect:
            nominal municipal registers claim full service coverage, while ground realities reveal severe crowding,
            degraded operating hours, or physical access bottlenecks.
          </p>
          <p>
            CivicPulse bridges this gap by unifying <strong>OpenStreetMap (OSM) spatial networks</strong>, <strong>administrative
            demographic records</strong>, and <strong>live citizen reports</strong> into an open, auditable analytics engine.
            This empowers city councils to move from reactive maintenance to evidence-driven civic infrastructure placement.
          </p>
        </div>
      </section>

      {/* Scoring Method Section */}
      <section id="scoring-method" className="space-y-6">
        <div className="border-b border-slate-200 pb-3">
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Calculator className="w-6 h-6 text-indigo-600" />
            Scoring Method
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Deterministic spatial formula, weight distributions, and composite evaluation pipelines.
          </p>
        </div>

        {/* 1. Formula Display */}
        <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl border border-indigo-900/50 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold tracking-wider uppercase">
              <Gauge className="w-4 h-4" />
              Core Analytical Formula
            </div>
            <span className="text-xs bg-indigo-500/20 text-indigo-200 px-2.5 py-0.5 rounded-full border border-indigo-500/30">
              Normalized Range: 0.0 – 100.0 pts
            </span>
          </div>

          <div className="bg-black/40 rounded-xl p-4 md:p-6 font-mono text-base md:text-lg text-emerald-300 overflow-x-auto border border-white/10 text-center leading-relaxed">
            <span className="text-white font-bold">Access Score</span> = (
            <span className="text-blue-300">0.30 &times; S<sub>travel</sub></span>) + (
            <span className="text-emerald-300">0.20 &times; S<sub>avail</sub></span>) + (
            <span className="text-purple-300">0.20 &times; S<sub>cap</sub></span>) + (
            <span className="text-amber-300">0.15 &times; S<sub>transit</sub></span>) + (
            <span className="text-rose-300">0.15 &times; S<sub>equity</sub></span>)
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            The composite Access Score is evaluated for each locality centroid across individual service categories
            (Healthcare, Education, Water, Transport). Every sub-score <span className="font-mono text-indigo-200">S<sub>i</sub></span> is
            independently normalized on a continuous scale from 0 to 100 before weighting.
          </p>
        </div>

        {/* 2. Weight Breakdown Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {/* Travel Time */}
          <div className="bg-white p-4 rounded-xl border border-blue-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                <Clock className="w-4 h-4" />
              </span>
              <span className="text-xl font-extrabold text-blue-600">30%</span>
            </div>
            <h4 className="font-semibold text-slate-900 text-sm">Travel Time</h4>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: '30%' }} />
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Door-to-door network transit duration to the nearest reachable facility.
            </p>
          </div>

          {/* Availability */}
          <div className="bg-white p-4 rounded-xl border border-emerald-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                <Activity className="w-4 h-4" />
              </span>
              <span className="text-xl font-extrabold text-emerald-600">20%</span>
            </div>
            <h4 className="font-semibold text-slate-900 text-sm">Availability</h4>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: '20%' }} />
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Operating status: Operational (100), Limited (60), Degraded (50), Closed (0).
            </p>
          </div>

          {/* Capacity */}
          <div className="bg-white p-4 rounded-xl border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                <Users className="w-4 h-4" />
              </span>
              <span className="text-xl font-extrabold text-purple-600">20%</span>
            </div>
            <h4 className="font-semibold text-slate-900 text-sm">Capacity &amp; Load</h4>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-purple-600 h-1.5 rounded-full" style={{ width: '20%' }} />
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Load ratio &amp; service pressure: Demand population vs. available capacity slots.
            </p>
          </div>

          {/* Transit */}
          <div className="bg-white p-4 rounded-xl border border-amber-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <Bus className="w-4 h-4" />
              </span>
              <span className="text-xl font-extrabold text-amber-600">15%</span>
            </div>
            <h4 className="font-semibold text-slate-900 text-sm">Transit Links</h4>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-amber-600 h-1.5 rounded-full" style={{ width: '15%' }} />
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Distance to multimodal transit stops (iBus, bus stops, metro corridors).
            </p>
          </div>

          {/* Equity */}
          <div className="bg-white p-4 rounded-xl border border-rose-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <span className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                <Scale className="w-4 h-4" />
              </span>
              <span className="text-xl font-extrabold text-rose-600">15%</span>
            </div>
            <h4 className="font-semibold text-slate-900 text-sm">Equity Index</h4>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div className="bg-rose-600 h-1.5 rounded-full" style={{ width: '15%' }} />
            </div>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Demographic vulnerability weighting to prioritize historically underserved cells.
            </p>
          </div>
        </div>

        {/* 3. Gap Score & Desert Tiers */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-amber-600" />
                Gap Score &amp; Service Desert Classification
              </h3>
              <p className="text-sm text-slate-500 mt-0.5">
                Quantifying unmet municipal demand and identifying critical infrastructure deserts.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 bg-slate-100 px-4 py-2 rounded-xl text-slate-800 font-mono text-sm font-semibold">
              Gap Score = 100 &minus; Access Score
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Well Served */}
            <div className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">Well Served</span>
                <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                  80 – 100
                </span>
              </div>
              <p className="text-xs text-emerald-900 leading-snug">
                Immediate access within 10 mins. Plentiful capacity and robust transit connectivity.
              </p>
              <div className="text-[11px] font-mono text-emerald-700 pt-1">
                Gap: 0.0 – 20.0
              </div>
            </div>

            {/* Adequate */}
            <div className="p-3.5 rounded-xl border border-sky-200 bg-sky-50/50 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sky-800 uppercase tracking-wider">Adequate</span>
                <span className="text-xs font-mono font-bold text-sky-700 bg-sky-100 px-2 py-0.5 rounded">
                  60 – 79
                </span>
              </div>
              <p className="text-xs text-sky-900 leading-snug">
                Acceptable 10–20 min transit. Minor off-peak congestion with balanced load.
              </p>
              <div className="text-[11px] font-mono text-sky-700 pt-1">
                Gap: 20.1 – 40.0
              </div>
            </div>

            {/* At Risk */}
            <div className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/50 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">At Risk</span>
                <span className="text-xs font-mono font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                  40 – 59
                </span>
              </div>
              <p className="text-xs text-amber-900 leading-snug">
                20–30 min travel time. High capacity strain or partial operational limitations.
              </p>
              <div className="text-[11px] font-mono text-amber-700 pt-1">
                Gap: 40.1 – 60.0
              </div>
            </div>

            {/* Underserved */}
            <div className="p-3.5 rounded-xl border border-orange-200 bg-orange-50/50 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-orange-800 uppercase tracking-wider">Underserved</span>
                <span className="text-xs font-mono font-bold text-orange-700 bg-orange-100 px-2 py-0.5 rounded">
                  20 – 39
                </span>
              </div>
              <p className="text-xs text-orange-900 leading-snug">
                30–45 min travel time. Significant transit friction or severe facility overcrowding.
              </p>
              <div className="text-[11px] font-mono text-orange-700 pt-1">
                Gap: 60.1 – 80.0
              </div>
            </div>

            {/* Critical Desert */}
            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/50 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-800 uppercase tracking-wider">Critical Desert</span>
                <span className="text-xs font-mono font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded">
                  0 – 19
                </span>
              </div>
              <p className="text-xs text-rose-900 leading-snug">
                No active facility within the 2.5 km catchment or facility indefinitely closed. Priority alert.
              </p>
              <div className="text-[11px] font-mono text-rose-700 pt-1">
                Gap: 80.1 – 100.0
              </div>
            </div>
          </div>
        </div>

        {/* 4. Assumptions & Model Parameters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Spatial & Speed Assumptions */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <Compass className="w-5 h-5 text-blue-600" />
              Routing &amp; Travel Speed Assumptions
            </h3>
            <ul className="space-y-3 text-sm text-slate-600">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Walking Speed:</strong> 4.5 km/h assumed baseline for pedestrian access models.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Public Transit Speed:</strong> 22.0 km/h average speed incorporating stops and dwelling (system default mode).
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Driving Speed:</strong> 35.0 km/h calibrated for typical urban arterial traffic.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Urban Circuity Detour Factor (1.30&times;):</strong> Euclidean/Haversine distances are scaled by 1.30 to model actual street grid topology.
                </span>
              </li>
            </ul>
          </div>

          {/* Distance Decay & Thresholds */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              Distance Decay &amp; Catchment Model
            </h3>
            <ul className="space-y-3 text-sm text-slate-600">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Catchment Radius Cutoff (2.5 km):</strong> Facilities beyond 2.5 km from the locality centroid are considered out-of-catchment for primary walk/transit access.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Transit Proximity Decay:</strong> Optimal within 1.0 km; degrades linearly up to a 5.0 km limit:
                  <code className="text-xs bg-slate-100 text-slate-800 px-1 py-0.5 rounded ml-1 font-mono">
                    max(0, 100 - (d / 5.0) &times; 80)
                  </code>
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Travel Time Stepped Decay:</strong> &le;10m: 100 pts &bull; 10–20m: 80 pts &bull; 20–30m: 60 pts &bull; 30–45m: 35 pts &bull; &gt;45m: 10 pts &bull; unreachable: 0 pts.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Routing Fallback:</strong> Live OSRM network engine with graceful zero-downtime failover to deterministic geometric approximation.
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Data Provenance & Trust Section */}
        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-slate-700" />
            Data Sources &amp; Trust Hierarchy
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="font-semibold text-slate-800 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                OpenStreetMap (OSM)
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Source for street road networks, pedestrian ways, public bus stops, clinics, and civic infrastructure footprints.
              </p>
              <div className="text-[11px] text-slate-400 font-mono">ODbL License &copy; Contributors</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="font-semibold text-slate-800 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                Municipal &amp; Census Records
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Official administrative ward boundaries, population census counts, and designated registered bed/staff capacities.
              </p>
              <div className="text-[11px] text-slate-400 font-mono">Government Open Data Portals</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-2">
              <div className="font-semibold text-slate-800 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Community Reports &amp; Audits
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Crowdsourced citizen reports capturing real-time operational outages, staffing shortages, and reality gap divergence.
              </p>
              <div className="text-[11px] text-slate-400 font-mono">CivicPulse Verification Pipeline</div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Metrics Summary */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-slate-700" />
          Metrics Glossary
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Accessibility Score</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Calculates the ease of reaching essential services (healthcare, education, water) based on geographic proximity, transit links, capacity limits, and physical barriers.
            </p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Equity Index</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Measures the distribution of resources across demographics to ensure historically underserved areas receive prioritized intervention.
            </p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Reality Gap</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              The delta between official capacity/status of a facility and the on-the-ground reality verified by community reports. Penalizes scores when critical outages are active.
            </p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Confidence Score</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              A dynamic score reflecting the reliability of data, weighted heavily by data source trust factors, community verification, and recent audit timelines.
            </p>
          </div>
        </div>
      </section>

      {/* Data & Trust */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">Data &amp; Trust</h2>
        <div className="bg-blue-50 p-6 rounded-xl border border-blue-100 text-blue-900 leading-relaxed text-sm">
          <h4 className="font-bold mb-2">OpenStreetMap Attribution</h4>
          <p className="mb-4">
            Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline hover:text-blue-700">OpenStreetMap contributors</a>. CivicPulse relies on open spatial data enriched by proprietary and community-sourced layers.
          </p>
          <h4 className="font-bold mb-2">City Coverage</h4>
          <p>
            Currently configured with detailed civic infrastructure for <strong>Indore, Madhya Pradesh</strong>, including Rajwada, Sarafa, Old Palasia, Vijay Nagar, and Bhanwarkuan localities.
          </p>
        </div>
      </section>
    </div>
  );
};

