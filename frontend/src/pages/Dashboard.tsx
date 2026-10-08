import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { CoreMetricsPanel } from '../components/metrics/CoreMetricsPanel';
import { RecommendationPanel } from '../components/analysis/RecommendationPanel';
import { ScaleSelector, AnalysisScale, DataUnavailableState } from '../components/analysis/ScaleSelector';

export const Dashboard = () => {
  const { user } = useAuth();
  const [scale, setScale] = useState<AnalysisScale>('City');

  const mockCoreMetrics = {
    accessibility: { id: 'm1', name: 'Accessibility Score', value: 72, label: '/ 100', confidence: 95 },
    gap: { id: 'm2', name: 'Service Gap', value: 28, label: '% underserved', confidence: 85 },
    equity: { id: 'm3', name: 'Equity Index', value: 65, label: '/ 100', confidence: 80 },
    confidence: { id: 'm4', name: 'Data Confidence', value: 89, label: '%', explanation: 'High trust from community validations' },
    realityGap: { id: 'm5', name: 'Reality Gap', value: 12, label: '% deviation', explanation: 'Official vs Community' },
    servicePressure: { id: 'm6', name: 'Avg Capacity Pressure', value: 85, label: '% utilization' },
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
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8">
      <div className="mb-4 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Civic Dashboard</h1>
          <p className="text-slate-500 mt-1">
            Welcome, {user?.name}. Viewing insights as <span className="font-semibold text-slate-700">{user?.role}</span>.
          </p>
        </div>
        <div className="flex gap-2">
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
        <>
          {/* Core Metrics */}
          <section>
            <h2 className="text-xl font-bold text-slate-800 mb-4">{scale} Overview</h2>
            <CoreMetricsPanel {...mockCoreMetrics} />
          </section>

          {/* Actionable Panels (Planner Focus) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <section>
              <RecommendationPanel interventions={mockInterventions} />
            </section>
            
            <section className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-900 mb-4">Underserved Neighbourhoods Ranking</h3>
              <div className="space-y-3">
                 {['East End', 'Northside', 'West Industrial'].map((hood, i) => (
                    <div key={hood} className="flex justify-between items-center p-3 border-b border-slate-100 last:border-0">
                      <div className="flex gap-3 items-center">
                        <span className="font-bold text-slate-400">#{i + 1}</span>
                        <span className="font-semibold text-slate-700">{hood}</span>
                      </div>
                      <span className="text-sm font-medium bg-red-100 text-red-700 px-2.5 py-1 rounded-md">Critical Gap</span>
                    </div>
                 ))}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
};
