import React from 'react';
import { Metric } from '../../types/models';

export interface MetricCardProps {
  metric: Metric;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  loading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, trend, trendValue, loading }) => {
  if (loading) {
    return <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 animate-pulse h-32"></div>;
  }

  return (
    <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{metric.name}</h4>
        {metric.confidence !== undefined && (
          <span className="text-xs font-medium px-2 py-1 bg-slate-100 text-slate-600 rounded-md">
            Conf: {metric.confidence}%
          </span>
        )}
      </div>
      
      <div className="flex items-end gap-3">
        <span className="text-3xl font-bold text-slate-900">{metric.value}</span>
        <span className="text-sm font-medium text-slate-600 mb-1">{metric.label}</span>
      </div>

      {(trend || metric.explanation) && (
        <div className="mt-4 text-sm text-slate-500">
          {trend && (
            <span className={`inline-flex items-center font-medium mr-2 ${trend === 'up' ? 'text-emerald-600' : trend === 'down' ? 'text-red-600' : 'text-slate-600'}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
            </span>
          )}
          {metric.explanation && <span>{metric.explanation}</span>}
        </div>
      )}
    </div>
  );
};
