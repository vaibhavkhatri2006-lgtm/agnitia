import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useCivicScore } from '../context/CivicScoreContext';
import { VoiceInput } from '../components/report/VoiceInput';
import { CivicScorePanel } from '../components/report/CivicScorePanel';
import {
  ShieldAlert, MapPin, Camera, CheckCircle2, Star, AlertCircle, X, Trash2,
  ChevronRight, Mic, FileText, TrendingUp, Sparkles
} from 'lucide-react';
import { cn } from '../lib/utils';

const CATEGORIES = [
  { value: 'healthcare', label: '🏥 Healthcare', description: 'Hospital, clinic, medical access' },
  { value: 'education', label: '🏫 Education', description: 'School, college, learning center' },
  { value: 'transport', label: '🚌 Transport', description: 'Bus stop, road, transit' },
  { value: 'water', label: '💧 Water & Sanitation', description: 'Water supply, drainage, sewage' },
  { value: 'market', label: '🛒 Market & Food', description: 'Market, ration shop, food access' },
  { value: 'roads', label: '🛣️ Roads & Footpaths', description: 'Potholes, broken footpath, signage' },
  { value: 'electricity', label: '⚡ Electricity', description: 'Power cuts, streetlights, wiring' },
  { value: 'safety', label: '🚨 Safety & Security', description: 'Crime, lighting, emergency response' },
  { value: 'waste', label: '🗑️ Waste Management', description: 'Garbage collection, landfill issues' },
  { value: 'other', label: '📋 Other Civic Issue', description: 'Any other public concern' },
];

const SEVERITY_OPTS = [
  { value: 'low', label: 'Low', description: 'Minor inconvenience', color: 'border-slate-300 bg-slate-50 text-slate-700', activeColor: 'border-slate-400 bg-slate-100 ring-2 ring-slate-300' },
  { value: 'medium', label: 'Medium', description: 'Needs attention', color: 'border-amber-200 bg-amber-50 text-amber-700', activeColor: 'border-amber-400 bg-amber-100 ring-2 ring-amber-200' },
  { value: 'high', label: 'High', description: 'Urgent concern', color: 'border-orange-200 bg-orange-50 text-orange-700', activeColor: 'border-orange-400 bg-orange-100 ring-2 ring-orange-200' },
  { value: 'critical', label: 'Critical', description: 'Emergency issue', color: 'border-red-200 bg-red-50 text-red-700', activeColor: 'border-red-400 bg-red-100 ring-2 ring-red-200' },
];

interface FormState {
  title: string;
  category: string;
  description: string;
  location: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  hasPhoto: boolean;
  photoName?: string;
}

interface FormErrors {
  title?: string;
  category?: string;
  description?: string;
  location?: string;
}

type SubmitState = 'idle' | 'submitting' | 'success' | 'duplicate' | 'error';

export const ReportPage = () => {
  const { user } = useAuth();
  const { submitReport, recentPoints, clearRecentPoints, scoreState } = useCivicScore();

  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [form, setForm] = useState<FormState>({
    title: '',
    category: '',
    description: '',
    location: '',
    severity: 'medium',
    hasPhoto: false,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitState, setSubmitState] = useState<SubmitState>('idle');
  const [lastPoints, setLastPoints] = useState(0);
  const [showScorePanel, setShowScorePanel] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateForm = (field: keyof FormState, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: undefined }));
  };

  const handleVoiceFill = (text: string) => {
    updateForm('description', text);
    // Smart auto-detect: look for keywords in transcript to suggest category
    const lower = text.toLowerCase();
    if (/hospital|clinic|doctor|medical|health/.test(lower)) updateForm('category', 'healthcare');
    else if (/school|college|education|teacher|student/.test(lower)) updateForm('category', 'education');
    else if (/bus|road|transport|traffic|commute/.test(lower)) updateForm('category', 'transport');
    else if (/water|pipe|drainage|sewage|flooding/.test(lower)) updateForm('category', 'water');
    else if (/market|ration|shop|food/.test(lower)) updateForm('category', 'market');
    else if (/pothole|footpath|street|road damage/.test(lower)) updateForm('category', 'roads');
    else if (/electricity|power|light|voltage/.test(lower)) updateForm('category', 'electricity');
    else if (/garbage|waste|trash|dump/.test(lower)) updateForm('category', 'waste');
    else if (/crime|safety|theft|robbery/.test(lower)) updateForm('category', 'safety');
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!form.title.trim() || form.title.trim().length < 5) {
      newErrors.title = 'Please enter a title with at least 5 characters.';
    }
    if (!form.category) {
      newErrors.category = 'Please select an issue category.';
    }
    if (!form.description.trim() || form.description.trim().length < 20) {
      newErrors.description = 'Please provide a description of at least 20 characters.';
    }
    if (!form.location.trim() || form.location.trim().length < 3) {
      newErrors.location = 'Please enter a location or area name.';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      updateForm('hasPhoto', true);
      updateForm('photoName', file.name);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitState('submitting');
    try {
      const result = await submitReport({
        title: form.title.trim(),
        category: form.category,
        description: form.description.trim(),
        location: form.location.trim(),
        severity: form.severity,
        hasPhoto: form.hasPhoto,
      });

      if (result.isDuplicate) {
        setSubmitState('duplicate');
        return;
      }

      setLastPoints(result.points);
      setSubmitState('success');
    } catch {
      setSubmitState('error');
    }
  };

  const resetForm = () => {
    setForm({ title: '', category: '', description: '', location: '', severity: 'medium', hasPhoto: false });
    setErrors({});
    setVoiceTranscript('');
    setSubmitState('idle');
    clearRecentPoints();
  };

  // Restrict to citizens and community members (but also allow admin/authority to view)
  const canSubmit = user?.role === 'Citizen' || user?.role === 'Community';

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Page Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <ShieldAlert className="w-6 h-6 text-blue-600" />
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Report Reality</h1>
                <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded-full font-semibold">Beta</span>
              </div>
              <p className="text-sm text-slate-500">
                Describe civic issues using voice or text. Your validated reports earn Civic Points and help direct real change.
              </p>
            </div>

            <button
              onClick={() => setShowScorePanel(!showScorePanel)}
              className="flex items-center gap-2 px-3.5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold rounded-xl shadow-sm hover:shadow-md transition-all shrink-0"
            >
              <Star className="w-4 h-4" />
              <span className="hidden sm:inline">Civic Score</span>
              <span className="font-bold">{scoreState.totalScore}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6">
        <div className={cn('grid gap-6', showScorePanel ? 'grid-cols-1 lg:grid-cols-[1fr_380px]' : 'grid-cols-1 max-w-3xl')}>
          {/* Main Form Column */}
          <div className="space-y-5">

            {/* Success state */}
            {submitState === 'success' && (
              <div className="bg-white rounded-2xl border border-emerald-200 shadow-sm overflow-hidden">
                <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-6 text-white text-center">
                  <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
                    <CheckCircle2 className="w-9 h-9" />
                  </div>
                  <h2 className="text-xl font-bold mb-1">Report Submitted! 🎉</h2>
                  <p className="text-emerald-100 text-sm">Your report is now pending community verification.</p>
                </div>
                <div className="p-6 text-center">
                  <div className="inline-flex items-center gap-2 px-5 py-3 bg-amber-50 border border-amber-200 rounded-2xl mb-4">
                    <Star className="w-5 h-5 text-amber-500" />
                    <span className="text-2xl font-bold text-amber-600">+{lastPoints}</span>
                    <span className="text-sm text-amber-700 font-medium">Civic Points Earned</span>
                  </div>
                  <p className="text-slate-500 text-sm mb-4">
                    Points breakdown: +10 (complete report){form.hasPhoto ? ', +5 (photo evidence)' : ''}{form.description.length > 100 ? ', +2 (detailed description)' : ''}{(form.severity === 'critical' || form.severity === 'high') ? ', +3 (priority issue)' : ''}
                  </p>
                  <div className="flex gap-3 justify-center">
                    <button
                      onClick={resetForm}
                      className="px-5 py-2.5 bg-blue-600 text-white font-semibold text-sm rounded-xl hover:bg-blue-700 transition"
                    >
                      Submit Another Report
                    </button>
                    <button
                      onClick={() => setShowScorePanel(true)}
                      className="px-5 py-2.5 bg-slate-100 text-slate-700 font-semibold text-sm rounded-xl hover:bg-slate-200 transition flex items-center gap-1.5"
                    >
                      <TrendingUp className="w-4 h-4" />
                      View Score
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Duplicate warning */}
            {submitState === 'duplicate' && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-800 text-sm">Duplicate Report Detected</p>
                  <p className="text-amber-700 text-sm mt-1">A similar report for this category and location was submitted recently. Points are only awarded once per unique issue. Please wait 30 minutes or change the location/category.</p>
                  <button onClick={() => setSubmitState('idle')} className="mt-2 text-sm text-amber-700 underline underline-offset-2">Go back to form</button>
                </div>
              </div>
            )}

            {/* Access Restricted */}
            {!canSubmit && submitState === 'idle' && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-800 text-sm">View Only — Authority/Admin Role</p>
                  <p className="text-amber-700 text-sm mt-1">Report submission is available to Citizens and Community members. You can view the Civic Score Panel and leaderboard.</p>
                </div>
              </div>
            )}

            {/* Form */}
            {(canSubmit || submitState === 'idle') && submitState !== 'success' && submitState !== 'duplicate' && (
              <form onSubmit={handleSubmit} className="space-y-5">

                {/* Voice Input */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Mic className="w-4 h-4 text-blue-600" />
                    <h2 className="text-sm font-bold text-slate-800">Step 1: Describe the Issue (Voice or Text)</h2>
                  </div>
                  <VoiceInput
                    transcript={voiceTranscript}
                    setTranscript={setVoiceTranscript}
                    onFillFromVoice={handleVoiceFill}
                  />
                </div>

                {/* Smart Form Fields */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-5">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <h2 className="text-sm font-bold text-slate-800">Step 2: Complete Report Details</h2>
                    <span className="ml-auto text-[10px] text-slate-400">* Required</span>
                  </div>

                  {/* Title */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Report Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={form.title}
                      onChange={e => updateForm('title', e.target.value)}
                      placeholder="e.g. Broken water pipe on MG Road near bus stand"
                      maxLength={120}
                      disabled={!canSubmit}
                      className={cn(
                        'w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition disabled:bg-slate-50 disabled:cursor-not-allowed',
                        errors.title ? 'border-red-300 bg-red-50' : 'border-slate-300'
                      )}
                    />
                    {errors.title && <p className="mt-1 text-xs text-red-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.title}</p>}
                  </div>

                  {/* Category */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Issue Category <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {CATEGORIES.map(cat => (
                        <button
                          key={cat.value}
                          type="button"
                          disabled={!canSubmit}
                          onClick={() => updateForm('category', cat.value)}
                          className={cn(
                            'flex items-start gap-2 p-2.5 rounded-xl border text-left transition text-xs disabled:cursor-not-allowed',
                            form.category === cat.value
                              ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                              : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
                          )}
                        >
                          <span className="text-base shrink-0 leading-none mt-0.5">{cat.label.split(' ')[0]}</span>
                          <div>
                            <div className="font-semibold text-slate-700">{cat.label.slice(3)}</div>
                            <div className="text-[10px] text-slate-400 mt-0.5">{cat.description}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                    {errors.category && <p className="mt-1 text-xs text-red-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.category}</p>}
                  </div>

                  {/* Location */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Location / Area <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        value={form.location}
                        onChange={e => updateForm('location', e.target.value)}
                        placeholder="e.g. Vijay Nagar, Indore or Near Big Bazaar"
                        disabled={!canSubmit}
                        className={cn(
                          'w-full pl-9 border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition disabled:bg-slate-50 disabled:cursor-not-allowed',
                          errors.location ? 'border-red-300 bg-red-50' : 'border-slate-300'
                        )}
                      />
                    </div>
                    {errors.location && <p className="mt-1 text-xs text-red-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.location}</p>}
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Detailed Description <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      rows={4}
                      value={form.description}
                      onChange={e => updateForm('description', e.target.value)}
                      placeholder={voiceTranscript ? 'Voice transcript appears here (editable), or type below...' : 'Describe what you see on the ground — the problem, who it affects, how long it has existed...'}
                      disabled={!canSubmit}
                      className={cn(
                        'w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition resize-none disabled:bg-slate-50 disabled:cursor-not-allowed',
                        errors.description ? 'border-red-300 bg-red-50' : 'border-slate-300'
                      )}
                    />
                    <div className="flex justify-between mt-1">
                      {errors.description
                        ? <p className="text-xs text-red-600 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.description}</p>
                        : <span className="text-[10px] text-slate-400">Minimum 20 characters. More detail = +2 bonus points.</span>
                      }
                      <span className={cn('text-[10px] font-mono', form.description.length > 100 ? 'text-emerald-600' : 'text-slate-400')}>
                        {form.description.length}/500
                      </span>
                    </div>
                  </div>

                  {/* Severity */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">Severity Level</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {SEVERITY_OPTS.map(opt => (
                        <button
                          key={opt.value}
                          type="button"
                          disabled={!canSubmit}
                          onClick={() => updateForm('severity', opt.value as any)}
                          className={cn(
                            'p-2.5 rounded-xl border text-center transition text-xs font-semibold disabled:cursor-not-allowed',
                            form.severity === opt.value ? opt.activeColor : opt.color
                          )}
                        >
                          <div className="capitalize">{opt.label}</div>
                          <div className="text-[10px] font-normal opacity-75 mt-0.5">{opt.description}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Photo Upload */}
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Camera className="w-4 h-4 text-blue-600" />
                    <h2 className="text-sm font-bold text-slate-800">Step 3: Add Photo Evidence</h2>
                    <span className="ml-auto text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-semibold">+5 pts</span>
                  </div>

                  {form.hasPhoto ? (
                    <div className="flex items-center gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
                      <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-emerald-800">Photo attached</p>
                        <p className="text-xs text-emerald-600 truncate">{form.photoName}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => { updateForm('hasPhoto', false); updateForm('photoName', ''); }}
                        className="text-slate-400 hover:text-slate-600 transition"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <div
                      onClick={() => canSubmit && fileInputRef.current?.click()}
                      className={cn(
                        'flex justify-center items-center px-6 py-8 border-2 border-dashed rounded-xl transition-colors',
                        canSubmit ? 'border-slate-300 hover:border-blue-400 hover:bg-blue-50/50 cursor-pointer' : 'border-slate-200 bg-slate-50 cursor-not-allowed'
                      )}
                    >
                      <div className="text-center">
                        <Camera className="mx-auto h-10 w-10 text-slate-300 mb-2" />
                        <p className="text-sm text-blue-600 font-semibold">Click to upload photo</p>
                        <p className="text-xs text-slate-400 mt-1">PNG, JPG up to 10MB — earns +5 Civic Points</p>
                      </div>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handlePhotoUpload}
                    disabled={!canSubmit}
                  />
                </div>

                {/* Points Preview + Submit */}
                {canSubmit && (
                  <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
                    {/* Points preview */}
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-bold text-blue-800">Estimated Points on Submission</span>
                      </div>
                      <div className="space-y-1 text-xs text-blue-700">
                        <div className="flex justify-between"><span>Complete report</span><span className="font-semibold">+10</span></div>
                        {form.hasPhoto && <div className="flex justify-between text-emerald-700"><span>Photo evidence</span><span className="font-semibold">+5</span></div>}
                        {form.description.trim().length > 100 && <div className="flex justify-between text-emerald-700"><span>Detailed description</span><span className="font-semibold">+2</span></div>}
                        {(form.severity === 'high' || form.severity === 'critical') && <div className="flex justify-between text-orange-700"><span>Priority issue</span><span className="font-semibold">+3</span></div>}
                        <div className="border-t border-blue-200 pt-1 flex justify-between font-bold text-blue-900">
                          <span>Total (before verification)</span>
                          <span>
                            +{10 + (form.hasPhoto ? 5 : 0) + (form.description.trim().length > 100 ? 2 : 0) + ((form.severity === 'high' || form.severity === 'critical') ? 3 : 0)}
                          </span>
                        </div>
                        <p className="text-[10px] text-blue-500 pt-1">Up to +10 more after community/authority verification</p>
                      </div>
                    </div>

                    {/* Trust note */}
                    <div className="flex items-start gap-2 p-3 bg-slate-50 rounded-lg mb-4 text-xs text-slate-600">
                      <ShieldAlert className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                      <span>Points are awarded only after submission. Duplicate, incomplete, or rejected reports receive zero points. Your report is labeled as <strong>community-submitted</strong> and will undergo verification.</span>
                    </div>

                    <div className="flex gap-3">
                      <button
                        type="submit"
                        disabled={submitState === 'submitting'}
                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm rounded-xl shadow-sm transition disabled:opacity-60"
                      >
                        {submitState === 'submitting' ? (
                          <>
                            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Submitting Report...
                          </>
                        ) : (
                          <>
                            <ShieldAlert className="w-4 h-4" />
                            Submit Report & Earn Points
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={resetForm}
                        className="px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold text-sm rounded-xl transition"
                        title="Clear form"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </form>
            )}
          </div>

          {/* Score Panel */}
          {showScorePanel && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  Your Civic Score
                </h2>
                <button
                  onClick={() => setShowScorePanel(false)}
                  className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <CivicScorePanel />
            </div>
          )}
        </div>

        {/* Show Score CTA when panel is hidden */}
        {!showScorePanel && scoreState.reports.length > 0 && (
          <div className="mt-6 max-w-3xl">
            <button
              onClick={() => setShowScorePanel(true)}
              className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl hover:shadow-lg transition-all"
            >
              <div className="flex items-center gap-3">
                <Star className="w-5 h-5 text-yellow-300" />
                <div className="text-left">
                  <div className="font-bold text-sm">View Your Civic Score — {scoreState.totalScore} pts</div>
                  <div className="text-xs text-blue-200">{scoreState.levelName} · {scoreState.reports.length} report{scoreState.reports.length !== 1 ? 's' : ''} submitted</div>
                </div>
              </div>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
