import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  MessageSquarePlus, Star, CheckCircle2, ChevronRight, ChevronLeft,
  Send, Trash2, Clock, ThumbsUp, ThumbsDown, AlertCircle, Lightbulb,
  Bug, Heart, Zap, BarChart3, User, Calendar, Filter, TrendingUp,
} from 'lucide-react';
import { cn } from '../lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

type FeedbackCategory =
  | 'general'
  | 'feature_request'
  | 'bug_report'
  | 'data_quality'
  | 'ui_ux'
  | 'performance'
  | 'accessibility';

type FeedbackStatus = 'submitted' | 'reviewed' | 'in_progress' | 'resolved';

interface FeedbackEntry {
  id: string;
  userId: string;
  userName: string;
  userRole: string;
  category: FeedbackCategory;
  subject: string;
  description: string;
  rating: number;          // 1–5
  featureArea: string;
  isAnonymous: boolean;
  status: FeedbackStatus;
  upvotes: number;
  submittedAt: string;
  response?: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const CATEGORIES: { value: FeedbackCategory; label: string; icon: React.FC<any>; color: string; desc: string }[] = [
  { value: 'general',         label: 'General',         icon: MessageSquarePlus, color: 'text-blue-600 bg-blue-50 border-blue-200',     desc: 'Overall impressions & suggestions' },
  { value: 'feature_request', label: 'Feature Request', icon: Lightbulb,         color: 'text-amber-600 bg-amber-50 border-amber-200',   desc: 'New feature or enhancement ideas' },
  { value: 'bug_report',      label: 'Bug Report',      icon: Bug,               color: 'text-red-600 bg-red-50 border-red-200',         desc: 'Something isn\'t working correctly' },
  { value: 'data_quality',    label: 'Data Quality',    icon: BarChart3,         color: 'text-purple-600 bg-purple-50 border-purple-200', desc: 'Inaccurate or missing civic data' },
  { value: 'ui_ux',           label: 'UI / UX',         icon: Heart,             color: 'text-pink-600 bg-pink-50 border-pink-200',      desc: 'Design, layout, or usability' },
  { value: 'performance',     label: 'Performance',     icon: Zap,               color: 'text-orange-600 bg-orange-50 border-orange-200', desc: 'Slow loading or lag issues' },
  { value: 'accessibility',   label: 'Accessibility',   icon: User,              color: 'text-teal-600 bg-teal-50 border-teal-200',      desc: 'Issues with accessibility features' },
];

const FEATURE_AREAS = [
  'Dashboard', 'Civic Map', 'Scenario Lab', 'Report Reality',
  'Methodology', 'CivicBot (Voice AI)', 'Civic Score System',
  'Authentication / Login', 'Data & Analytics', 'General App',
];

const STATUS_CONFIG: Record<FeedbackStatus, { label: string; color: string }> = {
  submitted:   { label: 'Submitted',   color: 'text-slate-600 bg-slate-100 border-slate-200' },
  reviewed:    { label: 'Reviewed',    color: 'text-blue-600 bg-blue-50 border-blue-200' },
  in_progress: { label: 'In Progress', color: 'text-amber-600 bg-amber-50 border-amber-200' },
  resolved:    { label: 'Resolved',    color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
};

const STORAGE_KEY = 'civicpulse_feedback_v1';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function loadFeedback(): FeedbackEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : seedDemoFeedback();
  } catch {
    return seedDemoFeedback();
  }
}

function saveFeedback(data: FeedbackEntry[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch { /* ignore */ }
}

function seedDemoFeedback(): FeedbackEntry[] {
  const demos: FeedbackEntry[] = [
    {
      id: 'demo_1',
      userId: 'demo',
      userName: 'Priya Sharma',
      userRole: 'Citizen',
      category: 'feature_request',
      subject: 'Add offline map caching',
      description: 'It would be great if the Civic Map could cache tiles for offline use, especially in areas with poor connectivity.',
      rating: 5,
      featureArea: 'Civic Map',
      isAnonymous: false,
      status: 'reviewed',
      upvotes: 12,
      submittedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      response: 'Great suggestion! We\'re exploring PWA support for offline mode in the next sprint.',
    },
    {
      id: 'demo_2',
      userId: 'demo2',
      userName: 'Rajesh Verma',
      userRole: 'Authority',
      category: 'data_quality',
      subject: 'Vijay Nagar hospital data outdated',
      description: 'A new dispensary opened in Vijay Nagar last month but it\'s not showing on the map. Please update the dataset.',
      rating: 3,
      featureArea: 'Civic Map',
      isAnonymous: false,
      status: 'in_progress',
      upvotes: 8,
      submittedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: 'demo_3',
      userId: 'demo3',
      userName: 'Anonymous User',
      userRole: 'Citizen',
      category: 'ui_ux',
      subject: 'Dashboard is hard to read on mobile',
      description: 'The charts and metrics panels overlap on small screens. Scrolling is also very jumpy.',
      rating: 2,
      featureArea: 'Dashboard',
      isAnonymous: true,
      status: 'submitted',
      upvotes: 5,
      submittedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    },
  ];
  saveFeedback(demos);
  return demos;
}

// ─── Star Rating Component ────────────────────────────────────────────────────

function StarRating({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hovered, setHovered] = useState(0);
  const labels = ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'];
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => onChange(star)}
            className="transition-transform hover:scale-110 focus:outline-none"
          >
            <Star
              className={cn(
                'w-7 h-7 transition-colors',
                (hovered || value) >= star ? 'text-amber-400 fill-amber-400' : 'text-slate-300'
              )}
            />
          </button>
        ))}
        {(hovered || value) > 0 && (
          <span className="ml-2 text-sm font-semibold text-amber-600">
            {labels[hovered || value]}
          </span>
        )}
      </div>
    </div>
  );
}

// ─── Feedback Card Component ──────────────────────────────────────────────────

function FeedbackCard({
  entry,
  onUpvote,
  isOwn,
}: {
  entry: FeedbackEntry;
  onUpvote: (id: string) => void;
  isOwn: boolean;
}) {
  const cat = CATEGORIES.find(c => c.value === entry.category);
  const CatIcon = cat?.icon ?? MessageSquarePlus;
  const status = STATUS_CONFIG[entry.status];

  return (
    <div className={cn(
      'bg-white rounded-2xl border p-4 shadow-sm transition-all hover:shadow-md',
      isOwn ? 'border-blue-200 ring-1 ring-blue-100' : 'border-slate-200'
    )}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className={cn('w-9 h-9 rounded-xl flex items-center justify-center border shrink-0', cat?.color)}>
          <CatIcon className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 leading-tight">{entry.subject}</h3>
              <div className="flex items-center flex-wrap gap-1.5 mt-1">
                <span className={cn('text-[10px] px-2 py-0.5 rounded-full border font-semibold', cat?.color)}>
                  {cat?.label}
                </span>
                <span className={cn('text-[10px] px-2 py-0.5 rounded-full border font-semibold', status.color)}>
                  {status.label}
                </span>
                <span className="text-[10px] text-slate-400">{entry.featureArea}</span>
                {isOwn && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-600 font-semibold">
                    Your Post
                  </span>
                )}
              </div>
            </div>
            {/* Star rating */}
            <div className="flex items-center gap-0.5 shrink-0">
              {[1, 2, 3, 4, 5].map(s => (
                <Star key={s} className={cn('w-3 h-3', s <= entry.rating ? 'text-amber-400 fill-amber-400' : 'text-slate-200')} />
              ))}
            </div>
          </div>

          {/* Description */}
          <p className="text-xs text-slate-600 mt-2 leading-relaxed line-clamp-2">{entry.description}</p>

          {/* Response from team */}
          {entry.response && (
            <div className="mt-2 p-2.5 bg-blue-50 border border-blue-200 rounded-xl">
              <p className="text-[10px] font-bold text-blue-700 mb-0.5">💬 Team Response:</p>
              <p className="text-xs text-blue-800">{entry.response}</p>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <User className="w-3 h-3" />
              <span>{entry.isAnonymous ? 'Anonymous' : entry.userName}</span>
              <span>·</span>
              <Calendar className="w-3 h-3" />
              <span>{new Date(entry.submittedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
            </div>
            <button
              onClick={() => onUpvote(entry.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-xs font-semibold text-slate-500 hover:text-blue-600 transition"
            >
              <ThumbsUp className="w-3 h-3" />
              {entry.upvotes}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export const FeedbackPage = () => {
  const { user } = useAuth();

  const [feedback, setFeedback] = useState<FeedbackEntry[]>(loadFeedback);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [submitted, setSubmitted] = useState(false);
  const [activeTab, setActiveTab] = useState<'submit' | 'feed'>('submit');
  const [filterCat, setFilterCat] = useState<FeedbackCategory | 'all'>('all');

  // Form state
  const [category, setCategory] = useState<FeedbackCategory>('general');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [rating, setRating] = useState(0);
  const [featureArea, setFeatureArea] = useState('General App');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Upvoted IDs (persist per session)
  const [upvotedIds, setUpvotedIds] = useState<Set<string>>(new Set());

  const validateStep1 = () => {
    const e: Record<string, string> = {};
    if (!subject.trim() || subject.trim().length < 5)
      e.subject = 'Please enter a subject of at least 5 characters.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const validateStep2 = () => {
    const e: Record<string, string> = {};
    if (!description.trim() || description.trim().length < 20)
      e.description = 'Please describe the feedback in at least 20 characters.';
    if (rating === 0)
      e.rating = 'Please rate your experience.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2);
    else if (step === 2 && validateStep2()) setStep(3);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate async submit
    await new Promise(r => setTimeout(r, 900));

    const newEntry: FeedbackEntry = {
      id: `fb_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      userId: user?.id ?? 'guest',
      userName: user?.name ?? 'User',
      userRole: user?.role ?? 'Citizen',
      category,
      subject: subject.trim(),
      description: description.trim(),
      rating,
      featureArea,
      isAnonymous,
      status: 'submitted',
      upvotes: 0,
      submittedAt: new Date().toISOString(),
    };

    const updated = [newEntry, ...feedback];
    setFeedback(updated);
    saveFeedback(updated);
    setIsSubmitting(false);
    setSubmitted(true);
  };

  const handleUpvote = (id: string) => {
    if (upvotedIds.has(id)) return; // prevent double upvote
    setUpvotedIds(prev => new Set([...prev, id]));
    setFeedback(prev => {
      const updated = prev.map(f => f.id === id ? { ...f, upvotes: f.upvotes + 1 } : f);
      saveFeedback(updated);
      return updated;
    });
  };

  const resetForm = () => {
    setStep(1);
    setSubmitted(false);
    setCategory('general');
    setSubject('');
    setDescription('');
    setRating(0);
    setFeatureArea('General App');
    setIsAnonymous(false);
    setErrors({});
  };

  const filtered = filterCat === 'all' ? feedback : feedback.filter(f => f.category === filterCat);
  const sortedFeed = [...filtered].sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime());

  // Stats
  const avgRating = feedback.length
    ? (feedback.reduce((s, f) => s + f.rating, 0) / feedback.length).toFixed(1)
    : '—';
  const resolvedCount = feedback.filter(f => f.status === 'resolved').length;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 md:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <MessageSquarePlus className="w-5 h-5 text-blue-600" />
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">Feedback Center</h1>
              </div>
              <p className="text-xs text-slate-500">
                Share your thoughts, report bugs, or suggest improvements to CivicPulse.
              </p>
            </div>

            {/* Stats strip */}
            <div className="hidden sm:flex items-center gap-4">
              {[
                { label: 'Total', value: feedback.length },
                { label: 'Avg Rating', value: avgRating },
                { label: 'Resolved', value: resolvedCount },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-lg font-bold text-slate-900">{s.value}</div>
                  <div className="text-[10px] text-slate-400 font-medium">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4 p-1 bg-slate-100 rounded-xl w-fit">
            {(['submit', 'feed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-4 py-1.5 text-xs font-semibold rounded-lg transition capitalize',
                  activeTab === tab
                    ? 'bg-white text-blue-700 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                )}
              >
                {tab === 'submit' ? '✏️ Submit Feedback' : `📋 All Feedback (${feedback.length})`}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 md:px-8 py-6">
        {/* ── SUBMIT TAB ── */}
        {activeTab === 'submit' && (
          <>
            {submitted ? (
              /* Success screen */
              <div className="max-w-md mx-auto text-center mt-8">
                <div className="w-20 h-20 bg-emerald-50 border-2 border-emerald-200 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 mb-2">Thank you, {isAnonymous ? 'Anonymous' : user?.name?.split(' ')[0]}! 🎉</h2>
                <p className="text-slate-500 text-sm mb-6">
                  Your feedback has been saved locally and will help improve CivicPulse. The team reviews all submissions weekly.
                </p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={resetForm}
                    className="px-5 py-2.5 bg-blue-600 text-white font-semibold text-sm rounded-xl hover:bg-blue-700 transition shadow-sm"
                  >
                    Submit Another
                  </button>
                  <button
                    onClick={() => { setActiveTab('feed'); resetForm(); }}
                    className="px-5 py-2.5 bg-slate-100 text-slate-700 font-semibold text-sm rounded-xl hover:bg-slate-200 transition"
                  >
                    View All Feedback
                  </button>
                </div>
              </div>
            ) : (
              <div className="max-w-2xl mx-auto">
                {/* Progress bar */}
                <div className="flex items-center gap-2 mb-6">
                  {[1, 2, 3].map(s => (
                    <React.Fragment key={s}>
                      <div className={cn(
                        'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all',
                        step >= s
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : 'bg-white border-slate-300 text-slate-400'
                      )}>
                        {step > s ? '✓' : s}
                      </div>
                      {s < 3 && (
                        <div className={cn(
                          'flex-1 h-1 rounded-full transition-all',
                          step > s ? 'bg-blue-600' : 'bg-slate-200'
                        )} />
                      )}
                    </React.Fragment>
                  ))}
                  <span className="ml-2 text-xs text-slate-400 font-medium">
                    {step === 1 ? 'Category & Subject' : step === 2 ? 'Details & Rating' : 'Review & Submit'}
                  </span>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* ── Step 1 ── */}
                  {step === 1 && (
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
                      <h2 className="text-sm font-bold text-slate-800">What type of feedback do you have?</h2>

                      {/* Category grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                        {CATEGORIES.map(cat => {
                          const Icon = cat.icon;
                          return (
                            <button
                              key={cat.value}
                              type="button"
                              onClick={() => setCategory(cat.value)}
                              className={cn(
                                'flex flex-col items-start gap-1.5 p-3 rounded-xl border text-left transition',
                                category === cat.value
                                  ? `${cat.color} ring-2 ring-offset-1 ring-current`
                                  : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/40'
                              )}
                            >
                              <Icon className={cn('w-4 h-4', category === cat.value ? '' : 'text-slate-400')} />
                              <div className="text-xs font-bold text-slate-800">{cat.label}</div>
                              <div className="text-[10px] text-slate-400 leading-tight">{cat.desc}</div>
                            </button>
                          );
                        })}
                      </div>

                      {/* Feature area */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Which area of the app does this relate to?
                        </label>
                        <select
                          value={featureArea}
                          onChange={e => setFeatureArea(e.target.value)}
                          className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                        >
                          {FEATURE_AREAS.map(a => <option key={a}>{a}</option>)}
                        </select>
                      </div>

                      {/* Subject */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Subject / Title <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={subject}
                          onChange={e => { setSubject(e.target.value); setErrors(p => ({ ...p, subject: '' })); }}
                          placeholder="Brief summary of your feedback..."
                          maxLength={120}
                          className={cn(
                            'w-full border rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                            errors.subject ? 'border-red-300 bg-red-50' : 'border-slate-300'
                          )}
                        />
                        {errors.subject && (
                          <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />{errors.subject}
                          </p>
                        )}
                        <div className="text-right mt-0.5 text-[10px] text-slate-400">{subject.length}/120</div>
                      </div>
                    </div>
                  )}

                  {/* ── Step 2 ── */}
                  {step === 2 && (
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
                      <h2 className="text-sm font-bold text-slate-800">Tell us more</h2>

                      {/* Description */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Detailed Description <span className="text-red-500">*</span>
                        </label>
                        <textarea
                          rows={5}
                          value={description}
                          onChange={e => { setDescription(e.target.value); setErrors(p => ({ ...p, description: '' })); }}
                          placeholder="Describe your feedback in detail. Include steps to reproduce if it's a bug, or what problem the feature would solve..."
                          className={cn(
                            'w-full border rounded-xl px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 transition',
                            errors.description ? 'border-red-300 bg-red-50' : 'border-slate-300'
                          )}
                        />
                        {errors.description && (
                          <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />{errors.description}
                          </p>
                        )}
                        <div className={cn('text-right mt-0.5 text-[10px]', description.length >= 20 ? 'text-emerald-600' : 'text-slate-400')}>
                          {description.length} chars {description.length >= 20 ? '✓' : '(min 20)'}
                        </div>
                      </div>

                      {/* Rating */}
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-2">
                          Overall Experience Rating <span className="text-red-500">*</span>
                        </label>
                        <StarRating value={rating} onChange={v => { setRating(v); setErrors(p => ({ ...p, rating: '' })); }} />
                        {errors.rating && (
                          <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />{errors.rating}
                          </p>
                        )}
                      </div>

                      {/* Anonymous toggle */}
                      <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <input
                          type="checkbox"
                          id="anon"
                          checked={isAnonymous}
                          onChange={e => setIsAnonymous(e.target.checked)}
                          className="h-4 w-4 rounded accent-blue-600"
                        />
                        <label htmlFor="anon" className="text-xs text-slate-700 font-medium select-none">
                          Submit anonymously — your name won't appear in the public feed
                        </label>
                      </div>
                    </div>
                  )}

                  {/* ── Step 3 Review ── */}
                  {step === 3 && (
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                      <h2 className="text-sm font-bold text-slate-800">Review your feedback</h2>

                      <div className="space-y-3 text-sm">
                        {[
                          { label: 'Category', value: CATEGORIES.find(c => c.value === category)?.label },
                          { label: 'Feature Area', value: featureArea },
                          { label: 'Subject', value: subject },
                          { label: 'Submitted as', value: isAnonymous ? 'Anonymous' : user?.name },
                        ].map(row => (
                          <div key={row.label} className="flex gap-3">
                            <span className="text-slate-400 font-medium w-28 shrink-0">{row.label}</span>
                            <span className="text-slate-800 font-semibold">{row.value}</span>
                          </div>
                        ))}
                        <div className="flex gap-3">
                          <span className="text-slate-400 font-medium w-28 shrink-0">Rating</span>
                          <div className="flex gap-0.5">
                            {[1, 2, 3, 4, 5].map(s => (
                              <Star key={s} className={cn('w-4 h-4', s <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-200')} />
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                        <p className="text-xs font-semibold text-slate-500 mb-1">Description</p>
                        <p className="text-sm text-slate-800 leading-relaxed">{description}</p>
                      </div>

                      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700">
                        ✅ Feedback is saved locally on your device in this demo environment. In production it would sync to the server.
                      </div>
                    </div>
                  )}

                  {/* Navigation buttons */}
                  <div className="flex items-center gap-3">
                    {step > 1 && (
                      <button
                        type="button"
                        onClick={() => setStep(s => (s - 1) as any)}
                        className="flex items-center gap-1.5 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm rounded-xl transition"
                      >
                        <ChevronLeft className="w-4 h-4" /> Back
                      </button>
                    )}

                    {step < 3 ? (
                      <button
                        type="button"
                        onClick={handleNext}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition shadow-sm"
                      >
                        Next <ChevronRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl transition shadow-sm disabled:opacity-60"
                      >
                        {isSubmitting ? (
                          <>
                            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Submitting...
                          </>
                        ) : (
                          <><Send className="w-4 h-4" /> Submit Feedback</>
                        )}
                      </button>
                    )}
                  </div>
                </form>
              </div>
            )}
          </>
        )}

        {/* ── FEED TAB ── */}
        {activeTab === 'feed' && (
          <div className="space-y-5">
            {/* Filter bar */}
            <div className="flex items-center gap-2 flex-wrap">
              <Filter className="w-4 h-4 text-slate-400" />
              <button
                onClick={() => setFilterCat('all')}
                className={cn(
                  'px-3 py-1.5 text-xs font-semibold rounded-lg border transition',
                  filterCat === 'all'
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300'
                )}
              >
                All ({feedback.length})
              </button>
              {CATEGORIES.map(cat => {
                const count = feedback.filter(f => f.category === cat.value).length;
                if (count === 0) return null;
                return (
                  <button
                    key={cat.value}
                    onClick={() => setFilterCat(cat.value)}
                    className={cn(
                      'px-3 py-1.5 text-xs font-semibold rounded-lg border transition',
                      filterCat === cat.value
                        ? 'bg-blue-600 border-blue-600 text-white'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300'
                    )}
                  >
                    {cat.label} ({count})
                  </button>
                );
              })}
            </div>

            {/* Summary stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { icon: <MessageSquarePlus className="w-4 h-4" />, label: 'Total Feedback', value: feedback.length, color: 'text-blue-600 bg-blue-50 border-blue-200' },
                { icon: <Star className="w-4 h-4" />, label: 'Avg Rating', value: avgRating, color: 'text-amber-600 bg-amber-50 border-amber-200' },
                { icon: <CheckCircle2 className="w-4 h-4" />, label: 'Resolved', value: resolvedCount, color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
                { icon: <TrendingUp className="w-4 h-4" />, label: 'In Progress', value: feedback.filter(f => f.status === 'in_progress').length, color: 'text-orange-600 bg-orange-50 border-orange-200' },
              ].map(s => (
                <div key={s.label} className={cn('flex items-center gap-2.5 px-3 py-2.5 rounded-xl border', s.color)}>
                  {s.icon}
                  <div>
                    <div className="text-lg font-bold">{s.value}</div>
                    <div className="text-[10px] font-medium opacity-75">{s.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Cards */}
            {sortedFeed.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <MessageSquarePlus className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm font-medium">No feedback in this category yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sortedFeed.map(entry => (
                  <FeedbackCard
                    key={entry.id}
                    entry={entry}
                    onUpvote={handleUpvote}
                    isOwn={entry.userId === user?.id}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
