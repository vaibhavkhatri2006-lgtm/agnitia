import React from 'react';
import { Metric } from '../../types/models';
import { Info } from 'lucide-react';

export interface MetricCardProps {
  metric: Metric;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  loading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, trend, trendValue, loading }) => {
  if (loading) {
    return <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 animate-pulse h-36"></div>;
  }

  // Determine if high value is "good" or "bad" based on metric name for simple state coloring
  const isNegativeMetric = metric.name.toLowerCase().includes('gap') || metric.name.toLowerCase().includes('pressure');
  
  // Calculate percentage for progress bar (assuming values are out of 100)
  const percentValue = Math.min(Math.max(metric.value, 0), 100);
  
  // Determine color state
  let stateColor = 'bg-blue-500';
  let textColor = 'text-blue-700';
  
  if (isNegativeMetric) {
    if (percentValue > 50) { stateColor = 'bg-red-500'; textColor = 'text-red-700'; }
    else if (percentValue > 25) { stateColor = 'bg-amber-500'; textColor = 'text-amber-700'; }
    else { stateColor = 'bg-emerald-500'; textColor = 'text-emerald-700'; }
  } else {
    if (percentValue > 75) { stateColor = 'bg-emerald-500'; textColor = 'text-emerald-700'; }
    else if (percentValue > 50) { stateColor = 'bg-amber-500'; textColor = 'text-amber-700'; }
    else { stateColor = 'bg-red-500'; textColor = 'text-red-700'; }
  }

  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md hover:border-blue-100 transition-all duration-200 flex flex-col justify-between group relative">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-1.5" title={metric.explanation}>
          <h4 className="text-[12px] font-bold text-slate-500 uppercase tracking-wide">{metric.name}</h4>
          {metric.explanation && (
            <Info className="w-3.5 h-3.5 text-slate-300 hover:text-slate-500 cursor-help transition-colors" />
          )}
        </div>
        {metric.confidence !== undefined && (
          <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-50 text-slate-500 rounded-md border border-slate-200">
            {metric.confidence}% Conf
          </span>
        )}
      </div>
      
      <div className="flex items-baseline gap-1.5 mb-3">
        <span className={`text-3xl font-extrabold tracking-tight ${textColor}`}>{metric.value}</span>
        <span className="text-xs font-semibold text-slate-400">{metric.label}</span>
      </div>

      {/* Compact Progress Indicator */}
      <div className="w-full bg-slate-100 rounded-full h-1.5 mb-1 overflow-hidden">
        <div className={`h-1.5 rounded-full ${stateColor}`} style={{ width: `${percentValue}%` }}></div>
      </div>

      {trend && trendValue && (
        <div className="mt-2 pt-2 border-t border-slate-50 text-xs flex items-center gap-1.5 font-medium">
          <span className={`inline-flex items-center justify-center w-4 h-4 rounded-full ${trend === 'up' ? 'bg-emerald-100 text-emerald-700' : trend === 'down' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
          <span className={trend === 'up' ? 'text-emerald-700' : trend === 'down' ? 'text-red-700' : 'text-slate-600'}>
            {trendValue}
          </span>
        </div>
      )}
    </div>
  );
};

