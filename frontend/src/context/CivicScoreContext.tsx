import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';

export interface CivicReport {
  id: string;
  title: string;
  category: string;
  description: string;
  location: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  hasPhoto: boolean;
  status: 'pending' | 'verified' | 'rejected';
  pointsAwarded: number;
  submittedAt: string;
  verifiedAt?: string;
}

export interface CivicBadge {
  id: string;
  name: string;
  description: string;
  icon: string;
  earnedAt: string;
  color: string;
}

export interface LeaderboardEntry {
  rank: number;
  name: string;
  score: number;
  reports: number;
  badge: string;
}

export interface CivicScoreState {
  totalScore: number;
  reports: CivicReport[];
  badges: CivicBadge[];
  level: number;
  levelName: string;
  nextLevelScore: number;
  progressPercent: number;
}

interface CivicScoreContextType {
  scoreState: CivicScoreState;
  recentPoints: number | null;
  submitReport: (report: Omit<CivicReport, 'id' | 'status' | 'pointsAwarded' | 'submittedAt'>) => Promise<{ success: boolean; points: number; isDuplicate: boolean }>;
  isDemoMode: boolean;
  leaderboard: LeaderboardEntry[];
  clearRecentPoints: () => void;
}

const CivicScoreContext = createContext<CivicScoreContextType | undefined>(undefined);

const LEVEL_THRESHOLDS = [
  { min: 0, max: 49, name: 'Observer', level: 1 },
  { min: 50, max: 149, name: 'Reporter', level: 2 },
  { min: 150, max: 299, name: 'Advocate', level: 3 },
  { min: 300, max: 499, name: 'Guardian', level: 4 },
  { min: 500, max: 999, name: 'Champion', level: 5 },
  { min: 1000, max: Infinity, name: 'Legend', level: 6 },
];

const BADGE_DEFINITIONS = [
  { id: 'first_report', name: 'First Report', description: 'Submitted your first civic report', icon: '🏁', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { id: 'photo_reporter', name: 'Photo Reporter', description: 'Submitted a report with photographic evidence', icon: '📸', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { id: 'five_reports', name: 'Civic Voice', description: 'Submitted 5 or more reports', icon: '📢', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { id: 'verified_reporter', name: 'Verified', description: 'Had a report verified by authorities', icon: '✅', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  { id: 'critical_alert', name: 'First Responder', description: 'Reported a critical severity issue', icon: '🚨', color: 'bg-red-100 text-red-700 border-red-200' },
];

const DEMO_LEADERBOARD: LeaderboardEntry[] = [
  { rank: 1, name: 'Priya Sharma', score: 820, reports: 47, badge: '🏆' },
  { rank: 2, name: 'Rajesh Verma', score: 615, reports: 33, badge: '🥈' },
  { rank: 3, name: 'Anita Patel', score: 490, reports: 28, badge: '🥉' },
  { rank: 4, name: 'Suresh Nair', score: 340, reports: 21, badge: '⭐' },
  { rank: 5, name: 'Demo Citizen', score: 180, reports: 12, badge: '✨' },
];

function computeLevel(score: number) {
  const lvl = LEVEL_THRESHOLDS.find(l => score >= l.min && score <= l.max) || LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1];
  const nextLvl = LEVEL_THRESHOLDS.find(l => l.level === lvl.level + 1);
  const progressPercent = nextLvl
    ? Math.round(((score - lvl.min) / (nextLvl.min - lvl.min)) * 100)
    : 100;
  return {
    level: lvl.level,
    levelName: lvl.name,
    nextLevelScore: nextLvl ? nextLvl.min : lvl.max,
    progressPercent,
  };
}

function checkBadges(reports: CivicReport[], currentBadges: CivicBadge[]): CivicBadge[] {
  const newBadges: CivicBadge[] = [...currentBadges];
  const earnedIds = new Set(currentBadges.map(b => b.id));

  if (reports.length >= 1 && !earnedIds.has('first_report')) {
    const def = BADGE_DEFINITIONS.find(b => b.id === 'first_report')!;
    newBadges.push({ ...def, earnedAt: new Date().toISOString() });
  }
  if (reports.some(r => r.hasPhoto) && !earnedIds.has('photo_reporter')) {
    const def = BADGE_DEFINITIONS.find(b => b.id === 'photo_reporter')!;
    newBadges.push({ ...def, earnedAt: new Date().toISOString() });
  }
  if (reports.length >= 5 && !earnedIds.has('five_reports')) {
    const def = BADGE_DEFINITIONS.find(b => b.id === 'five_reports')!;
    newBadges.push({ ...def, earnedAt: new Date().toISOString() });
  }
  if (reports.some(r => r.status === 'verified') && !earnedIds.has('verified_reporter')) {
    const def = BADGE_DEFINITIONS.find(b => b.id === 'verified_reporter')!;
    newBadges.push({ ...def, earnedAt: new Date().toISOString() });
  }
  if (reports.some(r => r.severity === 'critical') && !earnedIds.has('critical_alert')) {
    const def = BADGE_DEFINITIONS.find(b => b.id === 'critical_alert')!;
    newBadges.push({ ...def, earnedAt: new Date().toISOString() });
  }
  return newBadges;
}

export const CivicScoreProvider = ({ children }: { children: ReactNode }) => {
  const { user } = useAuth();
  const [reports, setReports] = useState<CivicReport[]>([]);
  const [badges, setBadges] = useState<CivicBadge[]>([]);
  const [totalScore, setTotalScore] = useState(0);
  const [recentPoints, setRecentPoints] = useState<number | null>(null);
  const [isDemoMode] = useState(true);

  const storageKey = user ? `civicpulse_score_${user.id}` : null;

  // Load persisted state
  useEffect(() => {
    if (!storageKey) return;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        setReports(parsed.reports || []);
        setBadges(parsed.badges || []);
        setTotalScore(parsed.totalScore || 0);
      }
    } catch { /* ignore */ }
  }, [storageKey]);

  // Persist on change
  useEffect(() => {
    if (!storageKey) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify({ reports, badges, totalScore }));
    } catch { /* ignore */ }
  }, [storageKey, reports, badges, totalScore]);

  const submitReport = useCallback(async (
    reportData: Omit<CivicReport, 'id' | 'status' | 'pointsAwarded' | 'submittedAt'>
  ): Promise<{ success: boolean; points: number; isDuplicate: boolean }> => {
    // Check for duplicates (same category + location within last 30 min)
    const thirtyMinAgo = Date.now() - 30 * 60 * 1000;
    const isDuplicate = reports.some(r =>
      r.category === reportData.category &&
      r.location.toLowerCase().trim() === reportData.location.toLowerCase().trim() &&
      new Date(r.submittedAt).getTime() > thirtyMinAgo
    );

    if (isDuplicate) {
      return { success: false, points: 0, isDuplicate: true };
    }

    // Calculate points
    let points = 10; // base for complete report
    if (reportData.hasPhoto) points += 5;
    if (reportData.description.trim().length > 100) points += 2; // bonus for detailed description
    if (reportData.severity === 'critical' || reportData.severity === 'high') points += 3;

    const newReport: CivicReport = {
      ...reportData,
      id: `report_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      status: 'pending',
      pointsAwarded: points,
      submittedAt: new Date().toISOString(),
    };

    // Try to submit to backend
    const backendBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    try {
      const token = localStorage.getItem('civicpulse_token');
      if (token) {
        await fetch(`${backendBase}/reports`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            title: reportData.title,
            description: reportData.description,
            category_id: 1,
            severity: reportData.severity,
            status: 'submitted',
            source_type: 'community',
          }),
        });
      }
    } catch {
      // Demo mode fallback — continue locally
    }

    setReports(prev => {
      const updated = [newReport, ...prev];
      const newBadges = checkBadges(updated, badges);
      setBadges(newBadges);
      return updated;
    });
    setTotalScore(prev => prev + points);
    setRecentPoints(points);

    return { success: true, points, isDuplicate: false };
  }, [reports, badges]);

  const clearRecentPoints = useCallback(() => setRecentPoints(null), []);

  const levelData = computeLevel(totalScore);
  const scoreState: CivicScoreState = {
    totalScore,
    reports,
    badges,
    ...levelData,
  };

  // Inject user into leaderboard at their rank
  const leaderboard = user
    ? DEMO_LEADERBOARD.map(e =>
        e.rank === 5 ? { ...e, name: user.name || 'You', score: Math.max(totalScore, e.score) } : e
      )
    : DEMO_LEADERBOARD;

  return (
    <CivicScoreContext.Provider value={{ scoreState, recentPoints, submitReport, isDemoMode, leaderboard, clearRecentPoints }}>
      {children}
    </CivicScoreContext.Provider>
  );
};

export const useCivicScore = () => {
  const context = useContext(CivicScoreContext);
  if (!context) throw new Error('useCivicScore must be used within CivicScoreProvider');
  return context;
};
