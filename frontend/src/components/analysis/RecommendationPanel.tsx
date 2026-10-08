import React from 'react';
import { Intervention } from '../../types/models';

interface RecommendationPanelProps {
  interventions: Intervention[];
  loading?: boolean;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({ interventions, loading }) => {
  if (loading) {
    return <div className="p-4 bg-white rounded-xl shadow-sm border border-slate-200 animate-pulse h-64"></div>;
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-bold text-slate-900 mb-4">AI Recommendations & Investment Priority</h3>
      {interventions.length === 0 ? (
        <p className="text-sm text-slate-500">No recommendations available for this scale.</p>
      ) : (
        <div className="space-y-4">
          {interventions.map((intervention, index) => (
            <div key={intervention.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border border-slate-100 rounded-lg hover:bg-slate-50 transition-colors">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center shrink-0">
                  {index + 1}
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-800">{intervention.type}</h4>
                  <p className="text-xs text-slate-500 mt-1">Cost: ${intervention.cost.toLocaleString()}</p>
                </div>
              </div>
              <div className="mt-3 sm:mt-0 flex gap-2">
                {intervention.expectedBenefit.map((benefit) => (
                  <span key={benefit.id} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    +{benefit.value} {benefit.name}
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
