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
    <div className="flex items-center gap-2">
      <label className="text-sm font-medium text-slate-700">Analysis Scale:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as AnalysisScale)}
        className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm font-medium text-slate-800"
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
  <div className="p-8 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50 text-center flex flex-col items-center justify-center min-h-[300px]">
    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
      <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
      </svg>
    </div>
    <h3 className="text-lg font-bold text-slate-900 mb-1">Data unavailable at this scale</h3>
    <p className="text-slate-500 max-w-sm">
      We do not currently have sufficient data or backend support for the <span className="font-semibold text-slate-700">{scale}</span> scale in this region.
    </p>
  </div>
);
