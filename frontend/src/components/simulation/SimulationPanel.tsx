import React from 'react';
import { Scenario } from '../../types/models';

interface SimulationPanelProps {
  scenario: Scenario | null;
  loading?: boolean;
}

export const SimulationPanel: React.FC<SimulationPanelProps> = ({ scenario, loading }) => {
  if (loading) {
    return <div className="p-4 bg-white rounded-xl shadow-sm border border-slate-200 animate-pulse h-48"></div>;
  }

  if (!scenario) {
    return (
      <div className="bg-slate-50 border border-slate-200 border-dashed rounded-xl p-8 text-center">
        <p className="text-slate-500 text-sm">Select or create a scenario to view simulation before/after results.</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Scenario Simulation</h3>
          <p className="text-sm text-slate-500">{scenario.name}</p>
        </div>
        <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-full border border-blue-100">
          Impact: +{scenario.impactScore}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
          <h4 className="font-semibold text-slate-700 mb-2">Before</h4>
          <p className="text-slate-600">Baseline metrics...</p>
        </div>
        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
          <h4 className="font-semibold text-emerald-800 mb-2">After</h4>
          <p className="text-emerald-700">Projected improvements...</p>
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center text-sm">
        <span className="text-slate-500">Required Budget</span>
        <span className="font-bold text-slate-900">${scenario.budgetRequired.toLocaleString()}</span>
      </div>
    </div>
  );
};
