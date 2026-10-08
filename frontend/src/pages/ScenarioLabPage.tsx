import React, { useState } from 'react';
import { SimulationPanel } from '../components/simulation/SimulationPanel';
import { Scenario } from '../types/models';
import { Activity, ShieldAlert, BarChart3, TrendingUp } from 'lucide-react';

export const ScenarioLabPage = () => {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);

  const mockScenarios: Scenario[] = [
    {
      id: 'sc1',
      name: 'Northside Clinic Expansion',
      description: 'Add 200 beds to Northside Clinic to relieve pressure on Central Hospital.',
      interventions: [],
      impactScore: 85,
      budgetRequired: 4500000
    },
    {
      id: 'sc2',
      name: 'East End Transport Link',
      description: 'New bus routes to connect underserved areas to major healthcare hubs.',
      interventions: [],
      impactScore: 62,
      budgetRequired: 1200000
    }
  ];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-8">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <Activity className="w-8 h-8 text-indigo-600" />
          Scenario Lab
        </h1>
        <p className="text-slate-500 mt-2">
          Test interventions and simulate their impact on accessibility, equity, and resilience.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-4">
          <h2 className="font-bold text-slate-800">Available Scenarios</h2>
          {mockScenarios.map(sc => (
            <div 
              key={sc.id} 
              onClick={() => setSelectedScenario(sc)}
              className={`p-4 rounded-xl border cursor-pointer transition-colors ${
                selectedScenario?.id === sc.id 
                  ? 'bg-indigo-50 border-indigo-200 shadow-sm' 
                  : 'bg-white border-slate-200 hover:border-indigo-200 hover:bg-slate-50'
              }`}
            >
              <h3 className="font-semibold text-slate-900">{sc.name}</h3>
              <p className="text-sm text-slate-500 mt-1">{sc.description}</p>
            </div>
          ))}

          <button className="w-full mt-4 bg-slate-900 text-white font-medium py-3 rounded-xl shadow-sm hover:bg-slate-800 transition-colors flex justify-center items-center gap-2">
            <TrendingUp className="w-4 h-4" /> Create Custom Scenario
          </button>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <SimulationPanel scenario={selectedScenario} />
          
          {selectedScenario && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-blue-600" /> Before/After Impact
                  </h3>
                  <div className="h-40 bg-slate-50 rounded-lg border border-slate-100 flex items-center justify-center">
                    <p className="text-slate-400 text-sm">Chart visualization goes here</p>
                  </div>
               </div>
               <div className="bg-white p-6 rounded-xl shadow-sm border border-amber-200 bg-amber-50/30">
                  <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-amber-600" /> Future-Risk & Resilience
                  </h3>
                  <p className="text-sm text-slate-700">
                    This scenario improves resilience against localized facility failures by 24%. It mitigates future risks associated with population growth in this district.
                  </p>
               </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
