import React from 'react';
import { Intervention } from '../../types/models';

interface RecommendationPanelProps {
  interventions: Intervention[];
  loading?: boolean;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({ interventions, loading }) => {
  if (loading) {
    return <div className="p-6 bg-white rounded-2xl shadow-sm border border-slate-200 animate-pulse h-64"></div>;
  }

  return (
    <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center border border-blue-100">
          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-slate-900 tracking-tight">AI Recommendations & Investment</h3>
      </div>
      
      {interventions.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
          <p className="text-sm font-medium text-slate-500">No recommendations available for this scale.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {interventions.map((intervention, index) => (
            <div key={intervention.id} className="group flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border border-slate-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all duration-200 bg-white">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-slate-50 group-hover:bg-blue-50 text-slate-600 group-hover:text-blue-700 font-bold flex items-center justify-center shrink-0 border border-slate-200 group-hover:border-blue-200 transition-colors">
                  {index + 1}
                </div>
                <div>
                  <h4 className="text-base font-semibold text-slate-900">{intervention.type.replace(/([A-Z])/g, ' $1').trim()}</h4>
                  <p className="text-sm font-medium text-slate-500 mt-0.5">Est. Cost: <span className="text-slate-700">${intervention.cost.toLocaleString()}</span></p>
                </div>
              </div>
              <div className="mt-4 sm:mt-0 ml-14 sm:ml-0 flex flex-wrap gap-2">
                {intervention.expectedBenefit.map((benefit) => (
                  <span key={benefit.id} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                    +{benefit.value}{benefit.label === 'pts' ? ' pts' : benefit.label} {benefit.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

