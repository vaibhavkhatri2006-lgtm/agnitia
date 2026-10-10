import React, { useState } from 'react';
import { fetchSimulation } from '../../services/mapDataProvider';
import { Activity, MapPin, CheckCircle2, TrendingUp, AlertTriangle } from 'lucide-react';

export const SimulationPanel = ({ selectedLocation, onSimulateComplete }: { selectedLocation: {lat: number, lng: number} | null, onSimulateComplete: (res: any) => void }) => {
  const [serviceType, setServiceType] = useState('healthcare');
  const [capacity, setCapacity] = useState(5000);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleSimulate = async () => {
    if (!selectedLocation) {
      setError('Please select a location on the map first.');
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const payload = {
        service_type: serviceType,
        latitude: selectedLocation.lat,
        longitude: selectedLocation.lng,
        scope: 'city',
        proposed_capacity: capacity,
      };
      const res = await fetchSimulation(payload);
      setResult(res);
      onSimulateComplete(res);
    } catch (err: any) {
      setError(err.message || 'Simulation failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col h-full overflow-y-auto">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-indigo-600" />
        <h2 className="text-lg font-bold text-slate-900">What-If Simulation</h2>
      </div>

      <p className="text-sm text-slate-500 mb-6">
        Simulate the impact of adding a new civic facility. Select a location on the map to begin.
      </p>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Selected Location</label>
          <div className={`text-sm px-3 py-2 rounded-lg border ${selectedLocation ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-slate-200 bg-slate-50 text-slate-500'}`}>
            {selectedLocation ? (
              <span className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-600" />
                {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
              </span>
            ) : 'Click anywhere on the map'}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Facility Type</label>
          <select 
            className="w-full text-sm border-slate-200 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500"
            value={serviceType}
            onChange={(e) => setServiceType(e.target.value)}
          >
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="transport">Transport</option>
            <option value="water">Water & Sanitation</option>
            <option value="market">Markets & Food</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Estimated Capacity (People Served)</label>
          <input 
            type="number" 
            className="w-full text-sm border-slate-200 rounded-lg p-2 focus:ring-indigo-500 focus:border-indigo-500"
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
            min="100"
            step="100"
          />
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      <button
        onClick={handleSimulate}
        disabled={isLoading || !selectedLocation}
        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            Running...
          </>
        ) : (
          <>
            <Activity className="w-4 h-4" />
            Run Impact Analysis
          </>
        )}
      </button>

      {result && (
        <div className="mt-8 border-t border-slate-100 pt-6">
          <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" />
            Simulation Results
          </h3>
          
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100">
              <div className="text-[10px] uppercase font-bold text-emerald-600 tracking-wider">Access Score Gain</div>
              <div className="text-2xl font-black text-emerald-700">+{result.impact.accessibility_improvement.toFixed(1)}</div>
            </div>
            <div className="bg-blue-50 p-3 rounded-xl border border-blue-100">
              <div className="text-[10px] uppercase font-bold text-blue-600 tracking-wider">New People Served</div>
              <div className="text-2xl font-black text-blue-700">+{result.impact.population_gaining_access.toLocaleString()}</div>
            </div>
            <div className="bg-amber-50 p-3 rounded-xl border border-amber-100">
              <div className="text-[10px] uppercase font-bold text-amber-600 tracking-wider">Gap Reduction</div>
              <div className="text-xl font-bold text-amber-700">-{result.impact.gap_reduction.toFixed(1)} pts</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded-xl border border-indigo-100">
              <div className="text-[10px] uppercase font-bold text-indigo-600 tracking-wider">Time Saved</div>
              <div className="text-xl font-bold text-indigo-700">-{result.impact.travel_time_improvement_minutes.toFixed(1)} min</div>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h4 className="text-sm font-bold text-slate-800 mb-2">Impact Analysis</h4>
            <p className="text-sm text-slate-600 leading-relaxed mb-3">{result.explanation}</p>
            
            <h5 className="text-xs font-bold text-slate-700 mb-1">Key Drivers:</h5>
            <ul className="text-xs text-slate-600 space-y-1">
              {result.primary_factors.map((f: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-800 flex gap-2">
            <span className="font-bold shrink-0">Note:</span>
            <span>These projections are estimates based on existing coverage and population density.</span>
          </div>
        </div>
      )}
    </div>
  );
};
