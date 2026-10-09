import React from 'react';

export type AnalysisScale = 'Local' | 'Neighbourhood' | 'District/Ward' | 'City' | 'Region/State' | 'Country' | 'Global';

interface ScaleSelectorProps {
  value: AnalysisScale;
  onChange: (scale: AnalysisScale) => void;
  availableScales: AnalysisScale[];
}

export const ScaleSelector: React.FC<ScaleSelectorProps> = ({ value, onChange, availableScales }) => {
  const allScales: AnalysisScale[] = ['Local', 'Neighbourhood', 'District/Ward', 'City', 'Region/State', 'Country', 'Global'];

  return (
    <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-200">
      <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Scale</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as AnalysisScale)}
        className="border-none bg-slate-50 hover:bg-slate-100 rounded-lg px-4 py-2 text-sm font-bold text-blue-900 focus:ring-2 focus:ring-blue-500 outline-none transition-colors cursor-pointer appearance-none pr-8 relative"
        style={{ backgroundImage: 'url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%231e3a8a%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.7rem top 50%', backgroundSize: '0.65rem auto' }}
      >
        {allScales.map(scale => (
          <option key={scale} value={scale} disabled={!availableScales.includes(scale)}>
            {scale} {!availableScales.includes(scale) ? '(Unavailable)' : ''}
          </option>
        ))}
      </select>
    </div>
  );
};

export const DataUnavailableState = ({ scale }: { scale: AnalysisScale }) => (
  <div className="p-10 border-2 border-dashed border-slate-200 rounded-2xl bg-white shadow-sm text-center flex flex-col items-center justify-center min-h-[400px]">
    <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-6 border border-slate-100">
      <svg className="w-10 h-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
      </svg>
    </div>
    <h3 className="text-xl font-bold text-slate-900 mb-2">Data unavailable at this scale</h3>
    <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
      We do not currently have sufficient data or backend support for the <span className="font-semibold text-slate-800">{scale}</span> scale in this region. Try selecting a broader scale like City or District.
    </p>
  </div>
);
