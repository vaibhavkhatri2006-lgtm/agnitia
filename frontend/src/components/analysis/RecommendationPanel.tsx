import React from 'react';
import { DashboardRecommendation } from '../../services/dashboardService';
import { Sparkles, MapPin, Users, TrendingUp, ShieldCheck } from 'lucide-react';

interface RecommendationPanelProps {
  recommendations: DashboardRecommendation[];
  loading?: boolean;
}

export const RecommendationPanel: React.FC<RecommendationPanelProps> = ({ recommendations, loading }) => {
  if (loading) {
    return (
      <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 animate-pulse space-y-4">
        <div className="h-6 bg-slate-200 rounded w-1/3"></div>
        <div className="h-20 bg-slate-100 rounded-xl"></div>
        <div className="h-20 bg-slate-100 rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            AI Priority Recommendations
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Algorithmic infrastructure allocations from Stage 4B recommendation engine.
          </p>
        </div>
        <span className="text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-lg border border-indigo-200">
          Ranked Interventions
        </span>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
          <p className="text-sm font-medium text-slate-500">No candidate interventions available for this scale.</p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {recommendations.map((rec) => (
            <div
              key={rec.candidate_id}
              className="group p-4 border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all duration-200 bg-white"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-2.5">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 font-extrabold flex items-center justify-center shrink-0 border border-indigo-200 text-xs shadow-2xs">
                    #{rec.rank}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-slate-900 flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-indigo-600" />
                        {rec.area_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200">
                        {rec.service_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                      Strategy: <span className="font-medium text-slate-700">{rec.strategy}</span>
                    </p>
                  </div>
                </div>

                {/* Expected Access Score Gain & Priority Metric */}
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                    +{rec.expected_gain_pts} pts Access Gain
                  </span>
                </div>
              </div>

              {/* Details & Population Reached */}
              <div className="flex flex-wrap items-center justify-between text-xs text-slate-600 pt-2.5 border-t border-slate-100 gap-2">
                <div className="flex items-center gap-1.5 text-slate-700">
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    Population Reached:{' '}
                    <strong className="text-slate-900 font-semibold">
                      {rec.population.toLocaleString()}
                    </strong>{' '}
                    residents
                  </span>
                </div>

                <div className="flex items-center gap-1 text-[11px] text-slate-500">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                  <span>Score: <strong className="text-slate-800">{rec.recommendation_score.toFixed(1)}/100</strong></span>
                </div>
              </div>

              {/* First reason if available */}
              {rec.reasons && rec.reasons.length > 0 && (
                <div className="mt-2 text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg border border-slate-100">
                  <span className="font-semibold text-slate-700">Primary Rationale: </span>
                  {rec.reasons[0]}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
