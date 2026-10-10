import React from 'react';
import { useCivicScore } from '../../context/CivicScoreContext';
import { Star, TrendingUp, Trophy, Shield, Award, ChevronRight, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

const STATUS_CONFIG = {
  pending: { label: 'Pending', icon: Clock, color: 'text-amber-600 bg-amber-50 border-amber-200' },
  verified: { label: 'Verified', icon: CheckCircle2, color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  rejected: { label: 'Rejected', icon: XCircle, color: 'text-red-600 bg-red-50 border-red-200' },
};

const SEVERITY_COLOR = {
  low: 'text-slate-500 bg-slate-50 border-slate-200',
  medium: 'text-amber-600 bg-amber-50 border-amber-200',
  high: 'text-orange-600 bg-orange-50 border-orange-200',
  critical: 'text-red-600 bg-red-50 border-red-200',
};

export const CivicScorePanel = () => {
  const { scoreState, leaderboard, isDemoMode } = useCivicScore();
  const { totalScore, level, levelName, nextLevelScore, progressPercent, badges, reports } = scoreState;

  return (
    <div className="space-y-5">
      {/* Demo mode notice */}
      {isDemoMode && (
        <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-700">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span><strong>Demo Mode:</strong> Scores are saved locally. In production, these sync with the server.</span>
        </div>
      )}

      {/* Score Card */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-5 text-white shadow-lg relative overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: `radial-gradient(circle at 80% 20%, white 1px, transparent 1px), radial-gradient(circle at 20% 80%, white 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }} />
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-blue-200 text-xs font-semibold uppercase tracking-wider mb-1">Civic Score</p>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-bold tracking-tight">{totalScore}</span>
                <span className="text-blue-300 text-sm mb-1.5">pts</span>
              </div>
            </div>
            <div className="text-center">
              <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-2xl mb-1">
                {level <= 1 ? '👁️' : level === 2 ? '📝' : level === 3 ? '📣' : level === 4 ? '🛡️' : level === 5 ? '🏆' : '⭐'}
              </div>
              <span className="text-xs text-blue-200 font-semibold">{levelName}</span>
            </div>
          </div>

          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs text-blue-200 mb-1">
              <span>Level {level}</span>
              <span>{totalScore} / {nextLevelScore} pts → Level {level + 1}</span>
            </div>
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-white rounded-full transition-all duration-700"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-3 mt-4">
            {[
              { label: 'Reports', value: reports.length },
              { label: 'Verified', value: reports.filter(r => r.status === 'verified').length },
              { label: 'Badges', value: badges.length },
            ].map(stat => (
              <div key={stat.label} className="bg-white/10 rounded-xl p-2.5 text-center">
                <div className="text-xl font-bold">{stat.value}</div>
                <div className="text-[10px] text-blue-200 font-medium">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Badges */}
      {badges.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2.5 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-amber-500" />
            Achievement Badges
          </h3>
          <div className="flex flex-wrap gap-2">
            {badges.map(badge => (
              <div
                key={badge.id}
                className={cn('flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border text-xs font-semibold', badge.color)}
                title={badge.description}
              >
                <span>{badge.icon}</span>
                <span>{badge.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {badges.length === 0 && (
        <div className="text-center py-4 border border-dashed border-slate-200 rounded-xl">
          <Award className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-xs text-slate-400 font-medium">Submit your first report to earn a badge!</p>
        </div>
      )}

      {/* Leaderboard */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-2.5 flex items-center gap-1.5">
          <Trophy className="w-4 h-4 text-amber-500" />
          Community Leaderboard
        </h3>
        <div className="border border-slate-200 rounded-xl overflow-hidden divide-y divide-slate-100">
          {leaderboard.map(entry => (
            <div
              key={entry.rank}
              className={cn(
                'flex items-center gap-3 px-3.5 py-2.5',
                entry.rank <= 3 ? 'bg-amber-50/50' : 'bg-white hover:bg-slate-50'
              )}
            >
              <span className="text-base w-5 text-center">{entry.badge}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-slate-800 truncate">{entry.name}</div>
                <div className="text-[10px] text-slate-400">{entry.reports} reports</div>
              </div>
              <div className="text-sm font-bold text-blue-600">{entry.score}<span className="text-[10px] text-slate-400 ml-0.5">pts</span></div>
            </div>
          ))}
        </div>
      </div>

      {/* Report History */}
      {reports.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2.5 flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            My Report History
          </h3>
          <div className="space-y-2">
            {reports.slice(0, 5).map(report => {
              const statusCfg = STATUS_CONFIG[report.status];
              const StatusIcon = statusCfg.icon;
              return (
                <div key={report.id} className="border border-slate-200 rounded-xl p-3 bg-white">
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-semibold text-slate-800 truncate">{report.title}</span>
                        <span className={cn('text-[10px] px-1.5 py-0.5 rounded-full border font-medium capitalize', SEVERITY_COLOR[report.severity])}>
                          {report.severity}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={cn('flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-medium', statusCfg.color)}>
                          <StatusIcon className="w-3 h-3" />
                          {statusCfg.label}
                        </span>
                        <span className="text-[10px] text-slate-400">{report.category}</span>
                        <span className="text-[10px] text-slate-400">{new Date(report.submittedAt).toLocaleDateString('en-IN')}</span>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-bold text-emerald-600">+{report.pointsAwarded}</div>
                      <div className="text-[10px] text-slate-400">pts</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
