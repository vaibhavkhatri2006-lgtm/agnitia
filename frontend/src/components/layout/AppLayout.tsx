import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LogOut, LayoutDashboard, Map as MapIcon, ShieldAlert, Activity, BookOpen } from 'lucide-react';
import { cn } from '../../lib/utils';

export const AppLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Civic Map', path: '/map', icon: MapIcon },
    { name: 'Methodology', path: '/methodology', icon: BookOpen },
    // Show 'Report Reality' only to citizens or community
    ...(user?.role === 'Citizen' || user?.role === 'Community' ? [{ name: 'Report Reality', path: '/report', icon: ShieldAlert }] : []),
    // Show 'Scenario Lab' only to authority or admin
    ...(user?.role === 'Authority' || user?.role === 'Admin' ? [{ name: 'Scenario Lab', path: '/scenario-lab', icon: Activity }] : []),
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg leading-none">C</span>
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-600 tracking-tight">
              CivicPulse
            </span>
          </div>

          <div className="flex items-center gap-6">
            <nav className="hidden md:flex gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    location.pathname === item.path
                      ? "bg-slate-100 text-blue-700"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  {item.name}
                </Link>
              ))}
            </nav>

            <div className="h-6 w-px bg-slate-200 hidden md:block"></div>

            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end">
                <span className="text-sm font-semibold text-slate-900">{user?.name}</span>
                <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">{user?.role}</span>
              </div>
              
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
                title="Log out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full mx-auto relative overflow-hidden flex flex-col">
        <div className="bg-blue-600 text-white text-xs font-medium py-1.5 px-4 text-center">
          <strong>Demo Environment:</strong> The data displayed in this application is simulated for demonstration purposes.
        </div>
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
