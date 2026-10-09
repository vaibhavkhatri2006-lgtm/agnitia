import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Role } from '../types/models';
import { Eye, EyeOff, Lock } from 'lucide-react';
import DarkVeil from '../components/ui/DarkVeil';

export const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('Citizen');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    
    setIsSubmitting(true);
    setTimeout(() => {
      login(email, role);
      navigate('/dashboard');
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-[#111111] font-sans flex flex-col relative overflow-hidden selection:bg-blue-500/30 selection:text-white">
      
      {/* Dynamic Background from React Bits */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-50">
        <DarkVeil />
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center relative z-10 px-4 sm:px-6">
        
        {/* Translucent Glassmorphism Auth Container */}
        <div className="w-full max-w-md p-8 sm:p-10 text-left bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-[0_8px_32px_0_rgba(0,0,0,0.4)]">
          
          <header className="mb-8 text-center">
            <p className="text-[11px] font-mono uppercase tracking-widest font-semibold text-blue-400 mb-2">
              WELCOME BACK
            </p>
            <h1 className="text-2xl sm:text-[28px] font-bold text-white tracking-tight leading-snug mb-2">
              Sign in to CivicPulse
            </h1>
            <p className="text-sm text-slate-300 leading-normal">
              Access your neighbourhood insights and civic planning tools.
            </p>
          </header>

          <form onSubmit={handleLogin} className="space-y-4">
            
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Email address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full px-3.5 py-2.5 text-sm text-white placeholder:text-slate-500 bg-white/5 border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors backdrop-blur-sm"
              />
            </div>
            
            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-xs font-semibold text-slate-300">
                  Password
                </label>
                <button type="button" className="text-xs font-medium text-blue-400 hover:text-blue-300 hover:underline focus:outline-none">
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-3.5 pr-10 py-2.5 text-sm text-white placeholder:text-slate-500 bg-white/5 border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors backdrop-blur-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Mock Auth Role Selector */}
            <div>
               <label htmlFor="role" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Mock Auth Role
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="w-full px-3.5 py-2.5 text-sm text-white bg-[#0a1b33] border border-white/10 rounded-md shadow-sm hover:border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="Citizen">Citizen</option>
                <option value="Community">Community Organization</option>
                <option value="Authority">Authority (Planner)</option>
                <option value="Admin">Administrator</option>
              </select>
            </div>

            {/* Remember Me */}
            <div className="flex items-center pt-1">
              <input
                id="remember-me"
                type="checkbox"
                className="h-4 w-4 rounded border-white/20 bg-transparent text-blue-500 focus:ring-blue-500"
              />
              <label htmlFor="remember-me" className="ml-2 block text-xs text-slate-300">
                Remember this workstation for 30 days
              </label>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 active:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#111111] focus:ring-blue-500 transition-colors"
              >
                {isSubmitting ? (
                  <>
                    Authenticating...
                    <svg className="animate-spin ml-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>

            {/* Divider */}
            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase font-semibold">
                <span className="bg-[#0f172a] px-3 text-slate-400 font-mono tracking-wider rounded-md backdrop-blur-md">OR</span>
              </div>
            </div>

            {/* Google SSO */}
            <div>
              <button
                type="button"
                className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-white/10 rounded-md bg-white/5 hover:bg-white/10 text-sm font-medium text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#111111] focus:ring-slate-400 transition-colors backdrop-blur-sm"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.36 24 12 24z"/>
                  <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.36 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                </svg>
                <span>Continue with Google</span>
              </button>
            </div>

            {/* SAML SSO Link */}
            <div className="text-center pt-2">
              <button
                type="button"
                className="text-xs font-medium text-slate-400 hover:text-white inline-flex items-center gap-1.5 focus:outline-none focus:underline transition-colors"
              >
                <Lock className="w-3 h-3 text-slate-500" />
                Log in with Municipal Agency SAML / SSO
              </button>
            </div>

            {/* Create Account Link */}
            <div className="pt-4 text-center">
              <p className="text-xs text-slate-400">
                Don't have an account?{' '}
                <a href="#create-account" className="font-semibold text-blue-400 hover:text-blue-300 hover:underline focus:outline-none transition-colors">
                  Create account
                </a>
              </p>
            </div>
          </form>
        </div>
      </main>

      {/* Footer Details - Floating above background */}
      <footer className="relative z-10 w-full py-6 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 text-[11px] text-slate-500 drop-shadow-md">
        <div className="flex items-center gap-3 sm:gap-4">
          <a href="#terms" className="hover:text-slate-300 transition-colors">Terms of Service</a>
          <span>•</span>
          <a href="#privacy" className="hover:text-slate-300 transition-colors">Spatial Data Privacy</a>
          <span>•</span>
          <a href="#security" className="hover:text-slate-300 transition-colors">Public Trust Policy</a>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-500/90 font-mono text-[10px]">
          <Lock className="w-3 h-3" />
          256-bit TLS Encrypted
        </div>
      </footer>
    </div>
  );
};
