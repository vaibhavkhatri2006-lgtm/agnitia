import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { CoreMetricsPanel } from '../components/metrics/CoreMetricsPanel';
import { RecommendationPanel } from '../components/analysis/RecommendationPanel';
import { ScaleSelector, AnalysisScale, DataUnavailableState } from '../components/analysis/ScaleSelector';
import { CivicMap } from '../components/map/CivicMap';
import { AnalyticsPanel } from '../components/analysis/AnalyticsPanel';

export const Dashboard = () => {
  const { user } = useAuth();
  const [scale, setScale] = useState<AnalysisScale>('City');

  const mockCoreMetrics = {
    accessibility: { id: 'm1', name: 'Accessibility Score', value: 72, label: '/ 100', confidence: 95, explanation: 'Measures ease of reaching essential services within a 15-minute walk.' },
    gap: { id: 'm2', name: 'Service Gap', value: 28, label: '% underserved', confidence: 85, explanation: 'Percentage of population lacking adequate access to core amenities.' },
    equity: { id: 'm3', name: 'Equity Index', value: 65, label: '/ 100', confidence: 80, explanation: 'Distribution fairness of public investments across demographics.' },
    confidence: { id: 'm4', name: 'Data Confidence', value: 89, label: '%', explanation: 'Reliability score based on recent community validations.' },
    realityGap: { id: 'm5', name: 'Reality Gap', value: 12, label: '% deviation', explanation: 'Discrepancy between official reports and community observations.' },
    servicePressure: { id: 'm6', name: 'Avg Capacity Pressure', value: 85, label: '% utilization', explanation: 'Current usage versus maximum designed capacity.' },
  };

  const mockInterventions = [
    {
      id: 'i1',
      type: 'NewFacility' as const,
      targetLocation: [51.5, -0.1] as [number, number],
      cost: 5000000,
      expectedBenefit: [{ id: 'b1', name: 'Accessibility', value: 15, label: 'pts' }]
    },
    {
      id: 'i2',
      type: 'UpgradeFacility' as const,
      targetLocation: [51.52, -0.08] as [number, number],
      cost: 1200000,
      expectedBenefit: [{ id: 'b2', name: 'Capacity', value: 30, label: '%' }]
    }
  ];

  const hasData = ['City', 'District/Ward'].includes(scale);

  return (
    <div className="p-4 md:p-8 max-w-[1400px] mx-auto space-y-10 selection:bg-blue-100 selection:text-blue-900">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">Civic Dashboard</h1>
          <p className="text-slate-500 mt-2 text-sm md:text-base">
            Welcome back, {user?.name}. Viewing insights as <span className="font-semibold text-slate-800">{user?.role}</span>.
          </p>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
           <ScaleSelector 
              value={scale} 
              onChange={setScale} 
              availableScales={['Local', 'Neighbourhood', 'District/Ward', 'City', 'Region/State', 'Country', 'Global']} 
           />
        </div>
      </div>

      {!hasData ? (
        <DataUnavailableState scale={scale} />
      ) : (
        <div className="space-y-10 animate-in fade-in duration-500">
          {/* Core Metrics */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">{scale} Overview</h2>
              <span className="px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-bold uppercase tracking-wider">Live</span>
            </div>
            <CoreMetricsPanel {...mockCoreMetrics} />
          </section>

          {/* Interactive Geographic Map */}
          <section>
             <div className="flex justify-between items-end mb-6">
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">Geospatial Analysis</h2>
            </div>
            <div className="h-[600px] w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-2">
              <CivicMap />
            </div>
          </section>

          {/* Analytics Data */}
          <section>
            <div className="flex justify-between items-end mb-6">
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">Analytics & Trends</h2>
            </div>
            <AnalyticsPanel coverageData={[]} accessibilityData={[]} historicalTrends={[]} />
          </section>

          {/* Actionable Panels (Planner Focus) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <section>
              <RecommendationPanel interventions={mockInterventions} />
            </section>
            
            <section className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-slate-900 tracking-tight">Underserved Neighbourhoods</h3>
                <span className="text-sm font-semibold text-slate-500">Ranking</span>
              </div>
              <div className="space-y-3 flex-1">
                 {['East End', 'Northside', 'West Industrial'].map((hood, i) => (
                    <div key={hood} className="group flex justify-between items-center p-4 border border-slate-100 rounded-xl hover:border-slate-300 transition-colors bg-slate-50/50 hover:bg-slate-50">
                      <div className="flex gap-4 items-center">
                        <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center shadow-sm">
                          <span className="font-bold text-slate-400 text-sm">#{i + 1}</span>
                        </div>
                        <span className="font-semibold text-slate-800">{hood}</span>
                      </div>
                      <span className="text-xs font-bold uppercase tracking-wide bg-red-50 text-red-700 px-3 py-1.5 rounded-lg border border-red-100">Critical Gap</span>
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
