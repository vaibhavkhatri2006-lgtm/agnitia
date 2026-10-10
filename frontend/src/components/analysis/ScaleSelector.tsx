import React from 'react';
import { Compass, AlertTriangle, ArrowRight } from 'lucide-react';

export type AnalysisScale = 'Local' | 'Neighbourhood' | 'District/Ward' | 'City' | 'Region/State' | 'Country' | 'Global';

interface ScaleSelectorProps {
  value: AnalysisScale;
  onChange: (scale: AnalysisScale) => void;
  availableScales: AnalysisScale[];
}

export const ScaleSelector: React.FC<ScaleSelectorProps> = ({ value, onChange, availableScales }) => {
  const allScales: AnalysisScale[] = ['City', 'District/Ward', 'Neighbourhood', 'Local', 'Region/State', 'Country', 'Global'];

  return (
    <div className="flex items-center gap-2.5 bg-white px-3.5 py-1.5 rounded-xl shadow-xs border border-slate-200">
      <Compass className="w-4 h-4 text-blue-600 shrink-0" />
      <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Spatial Scale:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as AnalysisScale)}
        className="border-none bg-slate-50 hover:bg-slate-100 rounded-lg px-3 py-1.5 text-xs font-bold text-blue-900 focus:ring-2 focus:ring-blue-500 outline-none transition-colors cursor-pointer appearance-none pr-8 relative"
        style={{
          backgroundImage:
            'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%231e3a8a%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E")',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 0.6rem top 50%',
          backgroundSize: '0.6rem auto',
        }}
      >
        {allScales.map((scale) => {
          const isSupported = availableScales.includes(scale);
          return (
            <option key={scale} value={scale}>
              {scale} {isSupported ? '✓ (Active Data)' : '⚠ (Unavailable)'}
            </option>
          );
        })}
      </select>
    </div>
  );
};

export const DataUnavailableState: React.FC<{
  scale: AnalysisScale;
  onSelectScale?: (scale: AnalysisScale) => void;
  message?: string;
}> = ({ scale, onSelectScale, message }) => (
  <div className="p-8 sm:p-12 border-2 border-dashed border-slate-200 rounded-3xl bg-white shadow-xs text-center flex flex-col items-center justify-center min-h-[420px] max-w-2xl mx-auto">
    <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center mb-5 border border-amber-200/60 shadow-xs">
      <AlertTriangle className="w-8 h-8 text-amber-600" />
    </div>
    
    <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold uppercase tracking-wider mb-2">
      Scope Tier: {scale}
    </span>
    
    <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight mb-2">
      Data Unavailable at {scale} Scale
    </h3>
    
    <p className="text-slate-600 text-sm sm:text-base max-w-lg mx-auto leading-relaxed mb-6">
      {message ||
        `Geographic scale '${scale}' is unavailable in the current municipal dataset. No official data exists at this tier. The active municipal dataset covers City, District/Ward, Neighbourhood, and Local cells.`}
    </p>

    {onSelectScale && (
      <div className="space-y-3 w-full max-w-md">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Switch to an active municipal scale:
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onSelectScale('Neighbourhood')}
            className="flex items-center justify-center gap-1.5 px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold rounded-xl border border-blue-200 transition-colors"
          >
            <span>Neighbourhood (5 Areas)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onSelectScale('District/Ward')}
            className="flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold rounded-xl border border-slate-200 transition-colors"
          >
            <span>District/Ward (4 Wards)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onSelectScale('Local')}
            className="flex items-center justify-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-bold rounded-xl border border-emerald-200 transition-colors"
          >
            <span>Local (4 Census Cells)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onSelectScale('City')}
            className="flex items-center justify-center gap-1.5 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold rounded-xl border border-indigo-200 transition-colors"
          >
            <span>City (Indore)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    )}
  </div>
);
