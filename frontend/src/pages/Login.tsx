import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Role } from '../types/models';
import { Eye, EyeOff, Lock, UserPlus, LogIn, Database, ShieldCheck, AlertCircle, KeyRound, Sparkles } from 'lucide-react';
import DarkVeil from '../components/ui/DarkVeil';

type AuthMode = 'login' | 'register' | 'reset';

export const Login = () => {
  const navigate = useNavigate();
  const { login, register, resetPassword, isAuthenticated, user, logout } = useAuth();

  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState<Role>('Authority');
  const [showPassword, setShowPassword] = useState(false);
  const [autoRegister, setAutoRegister] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === 'login') {
        try {
          // Attempt standard SQL database login
          await login(cleanEmail, password, role);
          setSuccessMessage('Authentication successful! Redirecting to dashboard...');
        } catch (loginErr: any) {
          const errMsg = loginErr.message || '';

          // If the account does not exist in SQL yet and autoRegister is enabled:
          if (
            autoRegister &&
            (errMsg.includes('Incorrect email or password') ||
              errMsg.includes('Invalid email') ||
              errMsg.includes('Incorrect email'))
          ) {
            try {
              // Try registering the user into SQL database automatically
              await register(cleanEmail, password, role, displayName || cleanEmail.split('@')[0]);
              setSuccessMessage(
                'New account detected! Successfully registered and saved in SQL database. Redirecting...'
              );
            } catch (regErr: any) {
              const regErrMsg = regErr.message || '';
              // If registration returns that account already exists, then the password was simply different!
              if (regErrMsg.includes('already exists')) {
                throw new Error(
                  'Password did not match existing SQL record. Click "Update Password & Sign In" below to sync with this password.'
                );
              }
              throw regErr;
            }
          } else {
            throw loginErr;
          }
        }
      } else if (mode === 'register') {
        // Explicit registration mode
        try {
          await register(cleanEmail, password, role, displayName || cleanEmail.split('@')[0]);
          setSuccessMessage('Account registered and stored in SQL database! Redirecting...');
        } catch (regErr: any) {
          const regErrMsg = regErr.message || '';
          if (regErrMsg.includes('already exists')) {
            throw new Error(
              'This email is already in the database. Use "Reset Password" or click "Update Password & Sign In" below.'
            );
          }
          throw regErr;
        }
      } else if (mode === 'reset') {
        // Explicit reset / sync password mode
        await resetPassword(cleanEmail, password, role);
        setSuccessMessage('Password successfully updated and verified in SQL! Redirecting...');
      }

      setTimeout(() => {
        navigate('/dashboard');
      }, 700);
    } catch (err: any) {
      setErrorMessage(err.message || 'Operation failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickReset = async () => {
    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setErrorMessage('Please ensure both email and password are provided above.');
      return;
    }
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await resetPassword(cleanEmail, password, role);
      setSuccessMessage('Password updated in SQL and signed in successfully! Redirecting...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 700);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOfflineFallback = () => {
    const cleanEmail = email.trim() || 'authority@example.com';
    const fallbackUser = {
      id: 'local_offline_' + Date.now(),
      name: displayName || cleanEmail.split('@')[0].toUpperCase(),
      email: cleanEmail,
      role: role || 'Authority',
    };
    localStorage.setItem('civicpulse_user', JSON.stringify(fallbackUser));
    localStorage.setItem('civicpulse_token', 'offline_session_token_' + Date.now());
    setSuccessMessage(`Entering offline session as ${fallbackUser.name} (${fallbackUser.role})...`);
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 500);
  };

  const handleDemoAutofill = (demoEmail: string, demoPass: string, demoRole: Role) => {
    setMode('login');
    setEmail(demoEmail);
    setPassword(demoPass);
    setRole(demoRole);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  return (
    <div className="min-h-screen bg-[#111111] font-sans flex flex-col relative overflow-hidden selection:bg-blue-500/30 selection:text-white">
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-50">
        <DarkVeil />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center relative z-10 px-4 sm:px-6 py-10">
        {/* Auth Container */}
        <div className="w-full max-w-md p-8 sm:p-10 text-left bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.4)]">
          {/* Header */}
          <header className="mb-6 text-center">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-400/20 text-[11px] font-mono uppercase tracking-wider font-semibold text-blue-400 mb-3">
              <Database className="w-3.5 h-3.5" />
              SQL Database Authenticated
            </div>
            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight leading-snug mb-1">
              {mode === 'login'
                ? 'Sign in to CivicPulse'
                : mode === 'register'
                ? 'Create CivicPulse Account'
                : 'Reset / Update Password'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-normal">
              {mode === 'login'
                ? 'Authenticate with your email & password stored in SQL.'
                : mode === 'register'
                ? 'Register your email & password to store them permanently in SQL.'
                : 'Update your password in SQL and sign in immediately.'}
            </p>
          </header>

          {/* If already logged in, show quick switcher banner */}
          {isAuthenticated && user && (
            <div className="mb-5 p-3 rounded-xl bg-blue-950/40 border border-blue-500/30 text-xs text-blue-200 flex items-center justify-between">
              <div>
                <span className="font-semibold text-white">Active Session:</span> {user.email} ({user.role})
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition"
                >
                  Dashboard
                </button>
                <button
                  type="button"
                  onClick={logout}
                  className="px-2.5 py-1 bg-white/10 hover:bg-white/20 text-slate-300 font-medium rounded-lg transition"
                >
                  Sign Out
                </button>
              </div>
            </div>
          )}

          {/* Mode Switcher Tabs */}
          <div className="grid grid-cols-3 gap-1 p-1 bg-white/5 border border-white/10 rounded-xl mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2 text-[11px] font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                mode === 'login'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <LogIn className="w-3.5 h-3.5" />
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2 text-[11px] font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                mode === 'register'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              Create
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('reset');
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2 text-[11px] font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                mode === 'reset'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <KeyRound className="w-3.5 h-3.5" />
              Reset Pass
            </button>
          </div>

          {/* Feedback Banners */}
          {errorMessage && (
            <div className="mb-4 p-3 rounded-lg bg-red-950/60 border border-red-500/40 text-red-200 text-xs flex flex-col gap-2 animate-fadeIn">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-red-300">Authentication Notice</p>
                  <p className="mt-0.5 text-red-100">{errorMessage}</p>
                </div>
              </div>

              {/* One-click Action to Sync / Reset Password */}
              {(errorMessage.includes('password') || errorMessage.includes('match') || errorMessage.includes('exists')) && (
                <div className="pt-2 border-t border-red-500/30 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={isSubmitting}
                    onClick={handleQuickReset}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg text-xs transition inline-flex items-center gap-1.5 shadow"
                  >
                    <KeyRound className="w-3.5 h-3.5" />
                    Update Password & Sign In with SQL
                  </button>
                </div>
              )}

              {/* One-click Fallback for Server Unreachable */}
              {(errorMessage.includes('unreachable') || errorMessage.includes('connection')) && (
                <div className="pt-2 border-t border-red-500/30 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={handleOfflineFallback}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg text-xs transition inline-flex items-center gap-1.5 shadow"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Enter Dashboard with Local Session ({role})
                  </button>
                </div>
              )}
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 text-xs flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Display Name (Register only) */}
            {mode === 'register' && (
              <div>
                <label htmlFor="displayName" className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Full Name / Display Name
                </label>
                <input
                  type="text"
                  id="displayName"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Vaibhav Khatri"
                  className="w-full px-3.5 py-2.5 text-sm text-white placeholder:text-slate-500 bg-white/5 border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors backdrop-blur-sm"
                />
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@gmail.com"
                className="w-full px-3.5 py-2.5 text-sm text-white placeholder:text-slate-500 bg-white/5 border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors backdrop-blur-sm"
              />
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-xs font-semibold text-slate-300">
                  {mode === 'reset' ? 'New Password' : 'Password'}
                </label>
                <span className="text-[11px] text-slate-400 font-mono">
                  Bcrypt Hashed in SQL
                </span>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder={
                    mode === 'reset'
                      ? 'Enter your new password to store in SQL'
                      : mode === 'register'
                      ? 'Choose an account password'
                      : 'Enter your password'
                  }
                  className="w-full pl-3.5 pr-10 py-2.5 text-sm text-white placeholder:text-slate-500 bg-white/5 border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors backdrop-blur-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white focus:outline-none"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Role Selector */}
            <div>
              <label htmlFor="role" className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                <span>Account Role & Permissions</span>
                <span className="text-[10px] text-blue-400 font-normal">Planner = Full GIS/Simulation Access</span>
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="w-full px-3.5 py-2.5 text-sm text-white bg-[#0a1b33] border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="Authority">Authority (Urban Planner & Decision Tools - Full Access)</option>
                <option value="Admin">Administrator (System Management)</option>
                <option value="Community">Community Organization (Verifier)</option>
                <option value="Citizen">Citizen (Public Access & Reporting)</option>
              </select>
            </div>

            {/* Auto-register toggle for Sign In mode */}
            {mode === 'login' && (
              <div className="flex items-center pt-1">
                <input
                  id="auto-register"
                  type="checkbox"
                  checked={autoRegister}
                  onChange={(e) => setAutoRegister(e.target.checked)}
                  className="h-4 w-4 rounded border-white/20 bg-transparent text-blue-500 focus:ring-blue-500 accent-blue-600"
                />
                <label htmlFor="auto-register" className="ml-2 block text-xs text-slate-300 select-none">
                  Auto-register and store in SQL if new user
                </label>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 active:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#111111] focus:ring-blue-500 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {mode === 'login'
                      ? 'Authenticating with SQL...'
                      : mode === 'register'
                      ? 'Saving to SQL Database...'
                      : 'Updating SQL Password...'}
                  </>
                ) : mode === 'login' ? (
                  'Sign In with SQL'
                ) : mode === 'register' ? (
                  'Create Account & Store in SQL'
                ) : (
                  'Update Password & Sign In with SQL'
                )}
              </button>
            </div>
          </form>

          {/* Pre-Seeded SQL Accounts */}
          <div className="mt-6 pt-5 border-t border-white/10">
            <p className="text-[11px] font-medium text-slate-400 mb-2.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                Quick Fill Seeded SQL Test Accounts:
              </span>
              <span className="text-[10px] text-slate-500">Instant Demo</span>
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoAutofill('authority@example.com', 'Authority123!', 'Authority')}
                className="px-2 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-400/20 text-[11px] text-blue-300 transition text-center truncate font-medium"
                title="authority@example.com"
              >
                Planner
              </button>
              <button
                type="button"
                onClick={() => handleDemoAutofill('admin@example.com', 'Admin123!', 'Admin')}
                className="px-2 py-1.5 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 border border-purple-400/20 text-[11px] text-purple-300 transition text-center truncate font-medium"
                title="admin@example.com"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleDemoAutofill('citizen@example.com', 'Citizen123!', 'Citizen')}
                className="px-2 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-slate-200 transition text-center truncate font-medium"
                title="citizen@example.com"
              >
                Citizen
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full py-6 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 text-[11px] text-slate-500 drop-shadow-md">
        <div className="flex items-center gap-3 sm:gap-4">
          <span className="text-slate-400">CivicPulse Indore GIS</span>
          <span>•</span>
          <span>Bcrypt Password Encryption</span>
          <span>•</span>
          <span>JWT Access Tokens</span>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-500/90 font-mono text-[10px]">
          <Lock className="w-3 h-3" />
          SQL DB Active (Port 8000)
        </div>
      </footer>
    </div>
  );
};
