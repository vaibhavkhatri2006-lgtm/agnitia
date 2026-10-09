import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

export interface CoverageData {
  category: string;
  coverage: number;
}

export interface AccessibilityData {
  neighbourhood: string;
  score: number;
}

export interface TrendData {
  date: string;
  gap: number;
}

interface AnalyticsPanelProps {
  coverageData?: CoverageData[];
  accessibilityData?: AccessibilityData[];
  historicalTrends?: TrendData[];
  loading?: boolean;
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({
  coverageData = [],
  accessibilityData = [],
  historicalTrends = [],
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="w-full h-96 bg-white rounded-2xl shadow-sm border border-slate-200 animate-pulse p-8">
        <div className="h-6 w-48 bg-slate-200 rounded mb-8"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
          <div className="h-48 bg-slate-100 rounded-xl"></div>
          <div className="h-48 bg-slate-100 rounded-xl"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 w-full">
      {/* Service Coverage by Category */}
      <section className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">Service Coverage</h3>
          <p className="text-sm text-slate-500 mt-1">Current coverage percentage by service category.</p>
        </div>
        <div className="flex-1 min-h-[300px]">
          {coverageData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={coverageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} domain={[0, 100]} />
                <Tooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="coverage" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} name="Coverage (%)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <span className="text-sm font-medium">No coverage data available</span>
            </div>
          )}
        </div>
      </section>

      {/* Accessibility Score Comparison */}
      <section className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">Neighbourhood Accessibility</h3>
          <p className="text-sm text-slate-500 mt-1">Comparative accessibility scores across areas.</p>
        </div>
        <div className="flex-1 min-h-[300px]">
          {accessibilityData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={accessibilityData} layout="vertical" margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis dataKey="neighbourhood" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} width={100} />
                <Tooltip
                  cursor={{ fill: '#f8fafc' }}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="score" fill="#10b981" radius={[0, 4, 4, 0]} barSize={24} name="Accessibility Score" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <span className="text-sm font-medium">No accessibility data available</span>
            </div>
          )}
        </div>
      </section>

      {/* Historical Trends */}
      <section className="bg-white p-6 sm:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col xl:col-span-2">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">Historical Service-Gap Trends</h3>
          <p className="text-sm text-slate-500 mt-1">Tracking the percentage of underserved populations over time.</p>
        </div>
        <div className="w-full min-h-[300px]">
          {historicalTrends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={historicalTrends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                <Line type="monotone" dataKey="gap" stroke="#ef4444" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} name="Service Gap (%)" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200 min-h-[300px]">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mb-3 border border-slate-200 shadow-sm">
                <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-slate-700">Historical records unavailable</span>
              <span className="text-xs text-slate-400 mt-1">Insufficient data to plot reliable historical trends for this region.</span>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
