import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { CoreMetricsPanel } from '../components/metrics/CoreMetricsPanel';
import { RecommendationPanel } from '../components/analysis/RecommendationPanel';
import { ScaleSelector, AnalysisScale, DataUnavailableState } from '../components/analysis/ScaleSelector';
import { CivicMap } from '../components/map/CivicMap';
import { AnalyticsPanel } from '../components/analysis/AnalyticsPanel';
import {
  fetchMultiScaleAnalytics,
  fetchUnderservedRankings,
  fetchDashboardRecommendations,
  buildDashboardCoreMetrics,
  buildDashboardChartsData,
  MultiScaleResult,
  UnderservedRanking,
  DashboardRecommendation,
} from '../services/dashboardService';
import { Activity, MapPin, Users, ShieldAlert, Sparkles } from 'lucide-react';

export const Dashboard = () => {
  const { user } = useAuth();
  const [scale, setScale] = useState<AnalysisScale>('Neighbourhood');
  const [multiScaleData, setMultiScaleData] = useState<MultiScaleResult | null>(null);
  const [rankings, setRankings] = useState<UnderservedRanking[]>([]);
  const [recommendations, setRecommendations] = useState<DashboardRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Supported municipal scales in current dataset
  const activeScales: AnalysisScale[] = ['City', 'District/Ward', 'Neighbourhood', 'Local'];

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setIsLoading(true);
      try {
        const [msResult, rankResult, recResult] = await Promise.all([
          fetchMultiScaleAnalytics(scale),
          fetchUnderservedRankings(5),
          fetchDashboardRecommendations('healthcare'),
        ]);
        if (isMounted) {
          setMultiScaleData(msResult);
          setRankings(rankResult);
          setRecommendations(recResult);
        }
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [scale]);

  const hasData = multiScaleData?.available ?? activeScales.includes(scale);

  // Derived metrics and charts data
  const coreMetrics = multiScaleData
    ? buildDashboardCoreMetrics(multiScaleData)
    : null;

  const chartsData = multiScaleData
    ? buildDashboardChartsData(multiScaleData)
    : { coverageData: [], accessibilityData: [], historicalTrends: [] };

  return (
    <div className="p-4 md:p-8 max-w-[1400px] mx-auto space-y-10 selection:bg-blue-100 selection:text-blue-900">
      {/* Dashboard Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
              <Activity className="w-3 h-3 text-blue-600" />
              CivicPulse Engine Active
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200">
              Role: {user?.role || 'Citizen'}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
            Civic Service Intelligence
          </h1>
          <p className="text-slate-500 mt-1 text-sm md:text-base">
            Multi-scale geospatial accessibility mapping, civic desert detection, and data-driven infrastructure interventions.
          </p>
        </div>

        {/* Spatial Scale Selector */}
        <div className="flex gap-2 w-full md:w-auto">
          <ScaleSelector
            value={scale}
            onChange={setScale}
            availableScales={activeScales}
          />
        </div>
      </div>

      {/* Main View: Active Data vs Safe No-Data State */}
      {!hasData ? (
        <DataUnavailableState
          scale={scale}
          onSelectScale={setScale}
          message={multiScaleData?.message}
        />
      ) : (
        <div className="space-y-10 animate-in fade-in duration-300">
          {/* Scale Summary Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white p-5 rounded-2xl shadow-sm border border-slate-700">
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-white/10 flex items-center justify-center border border-white/20 shrink-0">
                <MapPin className="w-6 h-6 text-indigo-300" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg sm:text-xl font-bold tracking-tight">
                    {scale} Geographic Scale Overview
                  </h2>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 uppercase tracking-wider">
                    {multiScaleData?.total_areas ?? 0} Areas Active
                  </span>
                </div>
                <p className="text-slate-300 text-xs sm:text-sm mt-0.5">
                  {multiScaleData?.message || `Analyzing civic service distribution at ${scale} administrative resolution.`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-medium text-slate-300 border-t sm:border-t-0 sm:border-l border-white/10 pt-3 sm:pt-0 sm:pl-5">
              <div className="flex items-center gap-1.5">
                <Users className="w-4 h-4 text-slate-400" />
                <span>
                  <strong className="text-white">
                    {multiScaleData?.total_population ? multiScaleData.total_population.toLocaleString() : '92,000'}
                  </strong>{' '}
                  Residents
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>
                  Avg Access:{' '}
                  <strong className="text-emerald-300">
                    {multiScaleData?.average_accessibility ? Math.round(multiScaleData.average_accessibility) : 74}/100
                  </strong>
                </span>
              </div>
            </div>
          </div>

          {/* Core Metrics */}
          {coreMetrics && (
            <section>
              <CoreMetricsPanel {...coreMetrics} loading={isLoading} />
            </section>
          )}

          {/* Interactive Geospatial Map */}
          <section>
            <div className="flex justify-between items-end mb-4">
              <div>
                <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
                  Geospatial Infrastructure Map
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Explore locality boundaries, verified facilities, OpenStreetMap Overpass amenities, and service deserts.
                </p>
              </div>
            </div>
            <div className="h-[600px] w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-2">
              <CivicMap />
            </div>
          </section>

          {/* Analytics Data & Charts */}
          <section>
            <div className="flex justify-between items-end mb-4">
              <div>
                <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
                  Accessibility & Coverage Analytics
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Comparative performance and multi-category infrastructure distributions at {scale} level.
                </p>
              </div>
            </div>
            <AnalyticsPanel
              coverageData={chartsData.coverageData}
              accessibilityData={chartsData.accessibilityData}
              historicalTrends={chartsData.historicalTrends}
              loading={isLoading}
            />
          </section>

          {/* Actionable Panels (Planner Focus & Critical Deserts) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <section>
              <RecommendationPanel recommendations={recommendations} loading={isLoading} />
            </section>

            <section className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-red-600" />
                    Underserved Areas Ranking
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Municipal areas prioritized by civic gap deficit and population exposure.
                  </p>
                </div>
                <span className="text-xs font-bold uppercase tracking-wider bg-red-50 text-red-700 px-2.5 py-1 rounded-lg border border-red-200">
                  Priority Leaderboard
                </span>
              </div>

              <div className="space-y-3 flex-1">
                {rankings.map((area) => (
                  <div
                    key={`${area.area_id}-${area.rank}`}
                    className="group flex justify-between items-center p-3.5 border border-slate-100 rounded-xl hover:border-slate-300 transition-colors bg-slate-50/60 hover:bg-slate-50"
                  >
                    <div className="flex gap-3.5 items-center">
                      <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center shadow-xs shrink-0">
                        <span className="font-bold text-slate-500 text-xs">#{area.rank}</span>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800 text-sm">{area.area_name}</span>
                          <span className="text-[10px] font-semibold text-slate-500 uppercase bg-slate-200/70 px-1.5 py-0.2 rounded">
                            {area.area_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Pop: {area.population.toLocaleString()} | Access: {Math.round(area.accessibility_score)}/100
                          {area.most_critical_category && (
                            <span className="ml-1 text-red-600 font-medium">
                              (Lagging: {area.most_critical_category})
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span
                        className={`text-xs font-bold uppercase tracking-wide px-2.5 py-1 rounded-lg border ${
                          area.gap_score >= 60
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : area.gap_score >= 40
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        }`}
                      >
                        {area.gap_score}% Gap
                      </span>
                      <span className="text-[10px] font-semibold text-slate-500">
                        {area.desert_classification}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
};
